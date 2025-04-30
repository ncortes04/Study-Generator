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
  { class: "icon-note-light", label: 0 },
  { class: "icon-discussion", label: 1 },
  { class: "icon-calendar-month", label: 2 },
  { class: "icon-assignment", label: 3 },
];

const viewportOptions = [
  { width: 1920, height: 1080 },
  { width: 2560, height: 1440 },
];

const IS_VAL_MODE = false;
const TOTAL_IMAGES = 500;

const outputDirImages = "test-generator/variable/images";
const outputDirLabels = "test-generator/variable/labels";
const outputDirTemps = "test-generator/tempImages";
const subfolder = IS_VAL_MODE ? "val" : "train";

const imgDir = path.join(outputDirImages, subfolder);
const labelDir = path.join(outputDirLabels, subfolder);

const resolutionOptions = [{ w: 512, h: 512 }];

[outputDirImages, outputDirLabels, outputDirTemps, imgDir, labelDir].forEach(
  (dir) => {
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  }
);

const cropAndAdjustBoxes = async (inputPath, outputPath, boxes) => {
  const imgMeta = await sharp(inputPath).metadata();
  const imgW = imgMeta.width;
  const imgH = imgMeta.height;

  const cropSizeOptions = [{ w: 512, h: 512 }];
  const cropChoice =
    cropSizeOptions[Math.floor(Math.random() * cropSizeOptions.length)];
  const cropW = Math.min(cropChoice.w, imgW);
  const cropH = Math.min(cropChoice.h, imgH);

  const cropAreaOptions = [
    { x: 0, y: 0 },
    { x: imgW - cropW, y: 0 },
    { x: 0, y: imgH - cropH },
    { x: imgW - cropW, y: imgH - cropH },
    { x: (imgW - cropW) / 2, y: (imgH - cropH) / 2 },
  ];
  const cropArea =
    cropAreaOptions[Math.floor(Math.random() * cropAreaOptions.length)];

  await sharp(inputPath)
    .extract({
      left: Math.round(cropArea.x),
      top: Math.round(cropArea.y),
      width: Math.round(cropW),
      height: Math.round(cropH),
    })
    .toFormat("jpeg")
    .toFile(outputPath);

  const newBoxes = [];

  for (const b of boxes) {
    const boxCenterX = b.cx * imgW;
    const boxCenterY = b.cy * imgH;
    const boxW = b.w * imgW;
    const boxH = b.h * imgH;

    const boxLeft = boxCenterX - boxW / 2;
    const boxTop = boxCenterY - boxH / 2;
    const boxRight = boxCenterX + boxW / 2;
    const boxBottom = boxCenterY + boxH / 2;

    const cropLeft = cropArea.x;
    const cropTop = cropArea.y;
    const cropRight = cropArea.x + cropW;
    const cropBottom = cropArea.y + cropH;

    const clippedLeft = Math.max(boxLeft, cropLeft);
    const clippedTop = Math.max(boxTop, cropTop);
    const clippedRight = Math.min(boxRight, cropRight);
    const clippedBottom = Math.min(boxBottom, cropBottom);

    const clippedW = clippedRight - clippedLeft;
    const clippedH = clippedBottom - clippedTop;

    if (clippedW > 10 && clippedH > 10) {
      const newCx = (clippedLeft + clippedW / 2 - cropLeft) / cropW;
      const newCy = (clippedTop + clippedH / 2 - cropTop) / cropH;
      const newW = clippedW / cropW;
      const newH = clippedH / cropH;

      // 🛡️ Check icon visibility
      if (b.icon) {
        const iconLeft = b.icon.x;
        const iconTop = b.icon.y;
        const iconRight = b.icon.x + b.icon.width;
        const iconBottom = b.icon.y + b.icon.height;

        const visibleLeft = Math.max(iconLeft, cropLeft);
        const visibleTop = Math.max(iconTop, cropTop);
        const visibleRight = Math.min(iconRight, cropRight);
        const visibleBottom = Math.min(iconBottom, cropBottom);

        const visibleWidth = Math.max(0, visibleRight - visibleLeft);
        const visibleHeight = Math.max(0, visibleBottom - visibleTop);
        const visibleArea = visibleWidth * visibleHeight;
        const totalArea = b.icon.width * b.icon.height;

        const visibleRatio = visibleArea / totalArea;

        if (visibleRatio < 0.5) {
          // ❌ If even one icon is less than 50% visible, REJECT
          return null;
        }
      } else {
        // ❌ No icon at all -> REJECT crop
        return null;
      }

      // ✅ Good box
      newBoxes.push({
        classId: b.classId,
        cx: newCx,
        cy: newCy,
        w: newW,
        h: newH,
      });
    }
  }

  return newBoxes;
};

(async () => {
  const browser = await puppeteer.launch({ headless: "new" });

  for (let i = 0; i < TOTAL_IMAGES; i++) {
    const page = await browser.newPage();
    const htmlPath = path.resolve(__dirname, "canvas-calendar.html");
    await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded" });
    const chosenViewport =
      viewportOptions[Math.floor(Math.random() * viewportOptions.length)];
    await page.setViewport({
      width: chosenViewport.width,
      height: chosenViewport.height,
    });
    ORIGINAL_HEIGHT = chosenViewport.height;
    ORIGINAL_WIDTH = chosenViewport.width;
    // Random calendar
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

        const weekRows = Array.from(
          document.querySelectorAll(".fc-content-skeleton tbody tr")
        ).slice(0, -3);

        const MAX_EVENTS = Math.floor(Math.random() * 20) + 10;
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

              // 🎯 30% chance to mark as completed
              // if (Math.random() < 0.3) {
              //   title.className = "fc-title calendar__event--completed";
              // } else {
              // }

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
        const icon = el.querySelector("i"); // get the icon inside the event
        const iconRect = icon ? icon.getBoundingClientRect() : null;
        let classId = parseInt(el.getAttribute("data-class-id")) || 0;
        const title = el.querySelector(".fc-title");
        // if (title && title.classList.contains("calendar__event--completed")) {
        //   classId = 5; // 🟢 mark as 'completed'
        // }
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          classId: classId,
          icon: iconRect
            ? {
                x: iconRect.x,
                y: iconRect.y,
                width: iconRect.width,
                height: iconRect.height,
              }
            : null,
        };
      });
    });

    const tempImagePath = path.join(outputDirTemps, `calendar_${i}.png`);
    await page.screenshot({ path: tempImagePath, type: "png" });
    const { width, height } = await sharp(tempImagePath).metadata();
    ORIGINAL_WIDTH = width;
    ORIGINAL_HEIGHT = height;

    const isCropped = Math.random() < 0.5;
    let chosen = 512;
    if (isCropped) {
      chosen =
        resolutionOptions[Math.floor(Math.random() * resolutionOptions.length)];
    }
    const TARGET_WIDTH = chosen.width;
    const TARGET_HEIGHT = chosen.height;

    // Decide random crop or not
    if (Math.random() < 1) {
      console.log(`✨ Cropping image ${i}`);
      const croppedOutputPath = path.join(imgDir, `calendar_${i}.jpg`); // ✅ save as normal name (no "_cropped")

      const normalizedBoxes = boxes.map((b) => {
        return {
          classId: b.classId,
          cx: (b.x + b.width / 2) / ORIGINAL_WIDTH,
          cy: (b.y + b.height / 2) / ORIGINAL_HEIGHT,
          w: b.width / ORIGINAL_WIDTH,
          h: b.height / ORIGINAL_HEIGHT,
          icon: b.icon,
        };
      });

      let finalBoxes = null;
      let retryCount = 0;
      const maxRetries = 10;

      while (
        (!finalBoxes || finalBoxes.length === 0) &&
        retryCount < maxRetries
      ) {
        finalBoxes = await cropAndAdjustBoxes(
          tempImagePath,
          croppedOutputPath,
          normalizedBoxes
        );
        retryCount++;
        if (!finalBoxes || finalBoxes.length === 0) {
          // <-- FIX this line too
          console.log(`🔁 Retry cropping attempt ${retryCount} for image ${i}`);
        }
      }

      fs.unlinkSync(tempImagePath); // Remove temp full screenshot

      if (!finalBoxes || finalBoxes.length === 0) {
        // <-- FIX this line too
        console.log(
          `⚠️ No valid boxes after ${maxRetries} retries for image ${i}, skipping...`
        );
        continue; // Skip saving this broken image
      }

      // ✅ Save cropped image and labels
      const labelLines = finalBoxes.map((b) => {
        return `${b.classId} ${b.cx.toFixed(6)} ${b.cy.toFixed(
          6
        )} ${b.w.toFixed(6)} ${b.h.toFixed(6)}`;
      });

      const labelPath = path.join(labelDir, `calendar_${i}.txt`);
      fs.writeFileSync(labelPath, labelLines.join("\n"));
    } else {
      console.log(`📸 Keeping full image ${i}`);
      const finalImgPath = path.join(imgDir, `calendar_${i}.jpg`);

      const scale = Math.min(
        TARGET_WIDTH / ORIGINAL_WIDTH,
        TARGET_HEIGHT / ORIGINAL_HEIGHT
      );
      const resizedW = Math.round(ORIGINAL_WIDTH * scale);
      const resizedH = Math.round(ORIGINAL_HEIGHT * scale);
      const padX = (TARGET_WIDTH - resizedW) / 2;
      const padY = (TARGET_HEIGHT - resizedH) / 2;

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
  }

  await browser.close();
})();
