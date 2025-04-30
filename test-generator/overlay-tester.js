const sharp = require("sharp");
const fs = require("fs");
const path = require("path");

const classNames = ["todo", "discussion", "class", "assignment"];

const imgDir = path.join("test-generator/variable/images", "val");
const labelDir = path.join("test-generator/variable/labels", "val");
const outputImagesDir = path.join("test-generator", "output_images_yolo_style");

if (!fs.existsSync(outputImagesDir))
  fs.mkdirSync(outputImagesDir, { recursive: true });

async function visualizeYOLOBoxes(imagePath, labelPath) {
  const image = sharp(imagePath);
  const { width: imgWidth, height: imgHeight } = await image.metadata();

  const labelData = fs.readFileSync(labelPath, "utf8");
  const lines = labelData.split("\n").filter((line) => line.trim() !== "");

  const composites = [];

  for (const line of lines) {
    const [clsIndex, cxNorm, cyNorm, wNorm, hNorm] = line
      .split(" ")
      .map(Number);
    const className = classNames[clsIndex] || "unknown";

    const cx = cxNorm * imgWidth;
    const cy = cyNorm * imgHeight;
    const boxWidth = wNorm * imgWidth;
    const boxHeight = hNorm * imgHeight;

    const x1 = cx - boxWidth / 2;
    const y1 = cy - boxHeight / 2;

    // 📦 Rectangle
    composites.push({
      input: Buffer.from(`
        <svg width="${imgWidth}" height="${imgHeight}">
          <rect x="${x1}" y="${y1}" width="${boxWidth}" height="${boxHeight}"
            stroke="lime" fill="none" stroke-width="2"/>
        </svg>
      `),
      left: 0,
      top: 0,
    });

    // 🏷️ Label with background for visibility
    composites.push({
      input: Buffer.from(`
        <svg width="${imgWidth}" height="${imgHeight}">
          <rect x="${x1}" y="${y1 - 24}" width="120" height="24" fill="yellow"/>
          <text x="${x1 + 4}" y="${
        y1 - 6
      }" font-size="16" font-weight="bold" fill="black">
            ${className}
          </text>
        </svg>
      `),
      left: 0,
      top: 0,
    });
  }

  const outputPath = path.join(outputImagesDir, path.basename(imagePath));
  await image.composite(composites).toFile(outputPath);
  console.log(`✅ Saved: ${outputPath}`);
}

async function visualizeAllImages() {
  const TOTAL_IMAGES = 50; // Adjust as needed
  for (let i = 0; i < TOTAL_IMAGES; i++) {
    const imgPath = path.join(imgDir, `calendar_${i}.jpg`);
    const txtPath = path.join(labelDir, `calendar_${i}.txt`);
    if (fs.existsSync(imgPath) && fs.existsSync(txtPath)) {
      await visualizeYOLOBoxes(imgPath, txtPath);
    }
  }
}

visualizeAllImages();
