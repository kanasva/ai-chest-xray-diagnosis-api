# AI Chest X-ray Diagnosis API

## TL;DR
This project provides 18-pathology diagnosis from chest x-rays using [TorchXRayVision](https://github.com/mlmed/torchxrayvision). It is deployed on AWS Lambda and must be accessed via a AWS SDK, as AWS API Gateway is not feasible due to exceeding the 30-second timeout limit when waking from a cold start.

## Features
- Diagnosis for **18 chest X-ray pathologies**, including Atelectasis, Cardiomegaly, Consolidation, Edema, Effusion, Emphysema, Enlarged Cardiomediastinum, Fibrosis, Fracture, Hernia, Infiltration, Lung Lesion, Lung Opacity, Mass, Nodule, Pleural Thickening, Pneumonia, and Pneumothorax.
- **Detection of out-of-distribution images** using an auto-encoder to prevent predictions on images that are different from the training data.
- **Grad-CAM** visualisation to highlight regions of interest in X-ray images


## Technologies
- [TorchXRayVision](https://github.com/mlmed/torchxrayvision): For chest X-ray analysis
- GitHub Actions
- Docker
- Terraform
- AWS Lambda

## How to use
- **Function name**: ai-chest-xray-diagnosis-api
- **Payload**
	- base64Img (string, required): The base64-encoded string of the chest x-ray image.
	- reconstructionThreshold (float, optional): The threshold for the reconstruction error to determine if the image is in-distribution. Default is 8000.
	- ssimThreshold (float, optional): The Structural Similarity Index (SSIM) threshold to determine if the image is in-distribution. Default is 0.62.
	- gradCamThreshold (float, optional): The threshold for pathology scores above which Grad-CAM images are generated. Default is 0.44.

- **Example Request**:
```
{
  "base64Img": "iVBORw0KGgoAAAANSUhEUgAAB4AAAAL...",
  "reconstructionThreshold": 8000,
  "ssimThreshold": 0.62,
  "gradCamThreshold": 0.44
}
```

- **Example Response (200 OK)**
```
{
  "reconstructionError": 3334.66796875,
  "ssim": 0.7661488930884929,
  "inDistribution": true,
  "prediction": {
    "Atelectasis": 0.5357859134674072,
    "Consolidation": 0.14535437524318695,
    "Infiltration": 0.5115969181060791,
    "Pneumothorax": 0.08925247937440872,
    "Edema": 0.0008359009516425431,
    "Emphysema": 0.5003246068954468,
    "Fibrosis": 0.5113949179649353,
    "Effusion": 0.11136345565319061,
    "Pneumonia": 0.0503874197602272,
    "Pleural_Thickening": 0.5349103212356567,
    "Cardiomegaly": 0.4702714681625366,
    "Nodule": 0.5080699920654297,
    "Mass": 0.5646909475326538,
    "Hernia": 0.995814323425293,
    "Lung Lesion": 0.0018308708677068353,
    "Fracture": 0.5114134550094604,
    "Lung Opacity": 0.2932303249835968,
    "Enlarged Cardiomediastinum": 0.10778136551380157
  },
  "gradCam": {
    "Atelectasis": "iVBORw0KGg...",
    "Infiltration": "iVBORw0...",
    "Emphysema": "iVBORw0KGg...",
    "Fibrosis": "iVBORw0KAAN...",
    "Pleural_Thickening": "iVBORw0K...",
    "Cardiomegaly": "iVBORw...",
    "Nodule": "iVBORw0KGg...",
    "Mass": "iVBORw0KGgoA...",
    "Hernia": "iVBORw0KG...",
    "Fracture": "iVBORw0KGgoA...",
  }
}
```





