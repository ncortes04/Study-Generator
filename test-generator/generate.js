const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const sharp = require("sharp");

const COLORS = ["red", "green", "blue", "teal"];
const TASK_NAMES = [
  " Homework",
  " WebAssign",
  " Essay",
  " Paper",
  " Quiz",
  " Test",
  " Reading",
  " Discussion",
  " Project",
];

const ICON_CLASSES = [
  { class: "icon-note-light", label: 0 }, // todo
  { class: "icon-discussion", label: 1 }, // class
  { class: "icon-calendar-month", label: 2 }, // assignment
];
const viewportOptions = [
  { width: 500, height: 800 }, // Mobile portrait
  { width: 768, height: 1024 }, // Tablet portrait
  { width: 1024, height: 768 }, // Tablet landscape
  { width: 1280, height: 720 }, // Laptop
  { width: 1440, height: 900 }, // Desktop
  { width: 1920, height: 1080 }, // Full HD desktop
];

const IS_VAL_MODE = true;
const TOTAL_IMAGES = 100;

const outputDirImages = "test-generator/variable/images";
const outputDirLabels = "test-generator/variable/labels";
const outputDirTemps = "test-generator/tempImages";
const subfolder = IS_VAL_MODE ? "val" : "train";

const imgDir = path.join(outputDirImages, subfolder);
const labelDir = path.join(outputDirLabels, subfolder);

const TARGET_WIDTH = 512;
const TARGET_HEIGHT = 512;

[outputDirImages, outputDirLabels, outputDirTemps, imgDir, labelDir].forEach(
  (dir) => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  }
);

console.log(`Generating ${IS_VAL_MODE ? "validation" : "training"} data:`);
console.log("Images →", imgDir);
console.log("Labels →", labelDir);

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });

  for (let i = 50; i <= TOTAL_IMAGES; i++) {
    const page = await browser.newPage();
    const htmlPath = path.resolve(__dirname, "canvas-calendar.html");
    await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded" });
    const chosenViewport =
      viewportOptions[Math.floor(Math.random() * viewportOptions.length)];
    await page.setViewport({
      width: chosenViewport.width,
      height: chosenViewport.height,
    });

    await page.evaluate(
      (COLORS, TASK_NAMES, ICON_CLASSES) => {
        const getRandomTime = () => {
          const hour = Math.floor(Math.random() * 12) + 1;
          const minutes = ["", ":00", ":15", ":30", ":45"][
            Math.floor(Math.random() * 5)
          ];
          const ampm = Math.random() > 0.5 ? "a" : "p";
          return `${hour}${minutes}${ampm}`;
        };

        let weekRows = Array.from(
          document.querySelectorAll(".fc-content-skeleton tbody tr")
        ).slice(0, -3);

        const MAX_EVENTS = Math.floor(Math.random() * 30) + 1;
        const MAX_EVENTS_PER_DAY = 4;
        let daysEventsMap = Array(21).fill(0);

        while (daysEventsMap.reduce((a, b) => a + b, 0) < MAX_EVENTS) {
          const idx = Math.floor(Math.random() * 21);
          if (daysEventsMap[idx] < MAX_EVENTS_PER_DAY) daysEventsMap[idx]++;
        }

        let dayIndex = 0;
        weekRows.forEach((row) => {
          row.querySelectorAll("td").forEach((td, index) => {
            for (let j = 0; j < daysEventsMap[dayIndex]; j++) {
              const task =
                TASK_NAMES[Math.floor(Math.random() * TASK_NAMES.length)];
              const color = COLORS[Math.floor(Math.random() * COLORS.length)];
              const iconData =
                ICON_CLASSES[Math.floor(Math.random() * ICON_CLASSES.length)];

              const a = document.createElement("a");
              a.className =
                "fc-day-grid-event fc-h-event fc-event fc-start fc-end event";
              a.title = task;
              a.style.borderColor = color;
              a.style.color = color;
              a.setAttribute("data-day-of-week", index);
              a.setAttribute("data-class-id", iconData.label);

              const content = document.createElement("div");
              content.className = "fc-content";

              const icon = document.createElement("i");
              icon.className = iconData.class;

              const time = document.createElement("span");
              time.className = "fc-time";
              time.innerText = getRandomTime();

              const title = document.createElement("span");
              title.className = "fc-title";
              title.innerText = task;

              content.appendChild(icon);
              content.appendChild(time);
              content.appendChild(title);
              a.appendChild(content);
              td.appendChild(a);
            }
            dayIndex++;
          });
        });
      },
      COLORS,
      TASK_NAMES,
      ICON_CLASSES
    );

    const boxes = await page.evaluate(() => {
      return Array.from(document.querySelectorAll(".event")).map((el) => {
        const rect = el.getBoundingClientRect();
        const classId = parseInt(el.getAttribute("data-class-id")) || 0;
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          classId: classId,
        };
      });
    });

    const tempImagePath = path.join(outputDirTemps, `calendar_${i}.png`);
    await page.screenshot({ path: tempImagePath, type: "png" });
    const ORIGINAL_WIDTH = chosenViewport.width;
    const ORIGINAL_HEIGHT = chosenViewport.height;

    const scale = Math.min(
      TARGET_WIDTH / ORIGINAL_WIDTH,
      TARGET_HEIGHT / ORIGINAL_HEIGHT
    );
    const resizedW = Math.round(ORIGINAL_WIDTH * scale);
    const resizedH = Math.round(ORIGINAL_HEIGHT * scale);
    const padX = (TARGET_WIDTH - resizedW) / 2;
    const padY = (TARGET_HEIGHT - resizedH) / 2;

    const finalImgPath = path.join(imgDir, `calendar_${i}.jpg`);
    await sharp(tempImagePath)
      .resize(TARGET_WIDTH, TARGET_HEIGHT, {
        fit: sharp.fit.contain,
        background: { r: 0, g: 0, b: 0 },
      })
      .toFormat("jpeg")
      .toFile(finalImgPath);

    fs.unlinkSync(tempImagePath);

    const labelLines = boxes
      .map((b) => {
        const x = b.x * scale + padX;
        const y = b.y * scale + padY;
        const w = b.width * scale;
        const h = b.height * scale;

        const cx = (x + w / 2) / TARGET_WIDTH;
        const cy = (y + h / 2) / TARGET_HEIGHT;
        const normW = w / TARGET_WIDTH;
        const normH = h / TARGET_HEIGHT;

        const xMin = cx - normW / 2;
        const xMax = cx + normW / 2;
        const yMin = cy - normH / 2;
        const yMax = cy + normH / 2;

        if (xMin >= 0 && xMax <= 1 && yMin >= 0 && yMax <= 1) {
          return `${b.classId} ${cx.toFixed(6)} ${cy.toFixed(
            6
          )} ${normW.toFixed(6)} ${normH.toFixed(6)}`;
        } else {
          return null; // Outside, discard
        }
      })
      .filter((line) => line !== null); // Remove null entries

    const labelPath = path.join(labelDir, `calendar_${i}.txt`);
    fs.writeFileSync(labelPath, labelLines.join("\n"));

    console.log(`✅ Saved ${finalImgPath} and ${labelPath}`);
    await page.close();
  }

  await browser.close();
})();
