const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const imgDir = path.join("test-generator", "images");
const labelDir = path.join("test-generator", "labels");
const outputImagesDir = path.join("test-generator", "output_images");

// Ensure the output directory exists
if (!fs.existsSync(outputImagesDir)) fs.mkdirSync(outputImagesDir);

// Function to draw bounding boxes on the image
async function visualizeBoundingBoxes(imagePath, labelPath) {
  const image = sharp(imagePath);

  const labels = fs
    .readFileSync(labelPath, "utf8")
    .split("\n")
    .filter((line) => line.trim() !== "");

  const imageMetadata = await image.metadata();
  const imgWidth = imageMetadata.width;
  const imgHeight = imageMetadata.height;
  console.log(imgWidth);
  console.log(imgHeight);

  const rectangles = labels.map((label) => {
    const [day, date, time, name, cx, cy, w, h] = label.split(" ").map(Number);
    const x1 = Math.floor((cx - w / 2) * imgWidth);
    const y1 = Math.floor((cy - h / 2) * imgHeight);
    const x2 = Math.floor((cx + w / 2) * imgWidth);
    const y2 = Math.floor((cy + h / 2) * imgHeight);

    return {
      input: Buffer.from(
        `<svg width="${x2 - x1}" height="${y2 - y1}">
          <rect x="0" y="0" width="${x2 - x1}" height="${
          y2 - y1
        }" stroke="red" fill="transparent" stroke-width="2" />
        </svg>`
      ),
      top: y1,
      left: x1,
    };
  });

  const imageWithBoxes = image.composite(rectangles);

  const outputImagePath = path.join(outputImagesDir, path.basename(imagePath));
  await imageWithBoxes.toFile(outputImagePath);

  console.log(`Image saved with bounding boxes: ${outputImagePath}`);
}

async function visualizeAllImages() {
  const TOTAL_IMAGES = 660;

  for (let i = 650; i < TOTAL_IMAGES; i++) {
    const imgPath = path.join(imgDir, `calendar_${i}.png`);
    const labelPath = path.join(labelDir, `calendar_${i}.txt`);

    if (fs.existsSync(imgPath) && fs.existsSync(labelPath)) {
      await visualizeBoundingBoxes(imgPath, labelPath);
    }
  }
}

visualizeAllImages();
