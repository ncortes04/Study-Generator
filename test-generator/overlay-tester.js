const sharp = require("sharp");
const fs = require("fs");
const path = require("path");
const xml2js = require("xml2js");

const imgDir = path.join("test-generator", "images");
const labelDir = path.join("test-generator", "labels");
const outputImagesDir = path.join("test-generator", "output_images");

// Ensure the output directory exists
if (!fs.existsSync(outputImagesDir)) fs.mkdirSync(outputImagesDir);

// Function to draw bounding boxes on the image
async function visualizeBoundingBoxes(imagePath, xmlPath) {
  const image = sharp(imagePath);
  // Parse the XML file to extract bounding boxes
  const xmlData = fs.readFileSync(xmlPath, "utf8");

  const parser = new xml2js.Parser();
  const jsonData = await parser.parseStringPromise(xmlData);

  const imageMetadata = await image.metadata();
  const imgWidth = imageMetadata.width;
  const imgHeight = imageMetadata.height;

  const rectangles = jsonData.annotation.object.map((obj) => {
    const { xmin, ymin, xmax, ymax } = obj.bndbox[0];

    // Convert to integer pixel values
    const x1 = parseInt(xmin[0]);
    const y1 = parseInt(ymin[0]);
    const x2 = parseInt(xmax[0]);
    const y2 = parseInt(ymax[0]);

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
  const TOTAL_IMAGES = 2;

  for (let i = 0; i < TOTAL_IMAGES; i++) {
    const imgPath = path.join(imgDir, `calendar_${i}.jpg`);
    const xmlPath = path.join(labelDir, `calendar_${i}.xml`);
    if (fs.existsSync(imgPath) && fs.existsSync(xmlPath)) {
      await visualizeBoundingBoxes(imgPath, xmlPath);
    }
  }
}

visualizeAllImages();
