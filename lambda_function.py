import json
import base64
import io
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
import torch
import torchxrayvision as xrv
import skimage.io
import torchvision.transforms
import numpy as np
from skimage.metrics import structural_similarity as ssim


def handler(event, context):

    try:
        """
        Prepare Image
        """
        base64_img = event["base64Img"]

        # Check if the base64 string is valid
        try:
            string_img = base64.b64decode(base64_img)
        except Exception as e:
            return response(501, error=str(e))

        # Prepare the image
        img_file = io.BytesIO(string_img)
        img = skimage.io.imread(img_file, plugin="imageio")
        img = xrv.datasets.normalize(
            img, 255
        )  # Convert 8-bit image to [-1024, 1024] range

        # Check if the image has color channels and convert to single color channel if needed
        if len(img.shape) == 3:
            img = img.mean(2)
        img = img[None, ...]  # Add a new axis for color channel

        # Apply transformations
        transform = torchvision.transforms.Compose(
            [xrv.datasets.XRayCenterCrop(), xrv.datasets.XRayResizer(224)]
        )
        img = transform(img)
        img = torch.from_numpy(img).unsqueeze(
            0
        )  # Convert to tensor and add batch dimension

        """
        Auto Encoder
        """
        reconstruction_threshold = event["reconstructionThreshold"]
        ssim_threshold = event["ssimThreshold"]

        # Load the autoencoder
        ae = xrv.autoencoders.ResNetAE(weights="101-elastic")

        # Get the autoencoder output for the new image
        out = ae(img)
        img_r = out["out"].detach().numpy()

        # Calculate reconstruction score (e.g., mean squared error)
        reconstruction_error = np.mean((img.numpy()[0][0] - img_r[0][0]) ** 2)

        # Calculate SSIM
        ssim_index = ssim(
            img.numpy()[0][0], img_r[0][0], data_range=img_r.max() - img_r.min()
        )

        # Define thresholds for reconstruction error and SSIM
        reconstruction_threshold = (
            8000  # This is an example, you need to determine a suitable threshold
        )
        ssim_threshold = (
            0.62  # This is an example, you need to determine a suitable threshold
        )

        in_distribution = (
            reconstruction_error <= reconstruction_threshold
            and ssim_index >= ssim_threshold
        )

        if in_distribution == False:
            body = {
                "reconstructionError": float(reconstruction_error),
                "ssim": float(ssim_index),
                "inDistribution": bool(in_distribution),
                "prediction": None,
                "gradcam": {None: None},
            }
            return response(200, body=body)

        """
        Prediction
        """
        # Load model and process image
        model = xrv.models.DenseNet(weights="densenet121-res224-all")
        outputs = model(img)

        # Convert results to dictionary
        output_dict = dict(zip(model.pathologies, outputs[0].detach().numpy()))
        output_dict_serializable = {k: v.item() for k, v in output_dict.items()}

        """
        Grad Cam
        """
        # Check for pathologies with values greater than 0.4
        grad_cam_threshold = event["gradCamThreshold"]
        relevant_pathologies = {
            key: value
            for key, value in output_dict_serializable.items()
            if value > grad_cam_threshold
        }

        gradcam_results = {}
        for pathology, score in relevant_pathologies.items():
            target = model.pathologies.index(pathology)
            img = img.requires_grad_()
            outputs = model(img)
            grads = torch.autograd.grad(outputs[:, target], img)[0][0][0]
            blurred = skimage.filters.gaussian(
                grads.detach().cpu().numpy() ** 2, sigma=(5, 5), truncate=3.5
            )

            # Create a custom colormap from viridis
            cmap = plt.cm.viridis
            cmap = cmap(np.arange(cmap.N))
            # Set alpha for low values to 0
            cmap[:128, -1] = np.linspace(0, 1, 128)
            # Create the new colormap
            cmap = mcolors.ListedColormap(cmap)

            my_dpi = 100
            fig = plt.figure(
                frameon=False, figsize=(224 / my_dpi, 224 / my_dpi), dpi=my_dpi
            )
            ax = plt.Axes(fig, [0.0, 0.0, 1.0, 1.0])
            ax.set_axis_off()
            fig.add_axes(ax)

            # Display the blurred gradient image
            ax.imshow(blurred, cmap=cmap, alpha=1)

            # Save the figure to base64
            buf = io.BytesIO()
            fig.savefig(buf, format="png")
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode("utf-8")
            plt.close(fig)
            gradcam_results[pathology] = img_str

        """
        Construct Response
        """
        body = {
            "reconstructionError": float(reconstruction_error),
            "ssim": float(ssim_index),
            "inDistribution": bool(in_distribution),
            "prediction": output_dict_serializable,
            "gradCam": gradcam_results,
        }
        return response(200, body=body)

    except Exception as e:
        return response(500, error=str(e))


def response(status_code, error=None, body=None):
    body = {"Error": error} if error else body
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
