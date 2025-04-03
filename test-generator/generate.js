const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");
const xml2js = require("xml2js");
const sharp = require("sharp");

const COLORS = ["red", "green", "blue", "teal"];
const TASK_NAMES = [
  "Homework",
  "WebAssign",
  "Essay",
  "Paper",
  "Quiz",
  "Test",
  "Reading",
  "Discussion",
  "Project",
];

const outputDir = "test-generator";
const imgDir = path.join(outputDir, "images");
const tempDir = path.join(outputDir, "tempImages"); // Temporary folder for PNG screenshots
const labelDir = path.join(outputDir, "labels");

// Ensure necessary directories exist
if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);
if (!fs.existsSync(imgDir)) fs.mkdirSync(imgDir);
if (!fs.existsSync(labelDir)) fs.mkdirSync(labelDir);
if (!fs.existsSync(tempDir)) fs.mkdirSync(tempDir); // Make sure the temp directory exists

const TOTAL_IMAGES = 400;

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
  });
  const pagePromises = [];

  for (let i = 100; i < TOTAL_IMAGES; i++) {
    const pagePromise = async () => {
      const page = await browser.newPage();
      const htmlPath = path.resolve(__dirname, "canvas-calendar.html");
      await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded" });
      await page.setViewport({ width: 800, height: 600 });

      await page.evaluate(
        (COLORS, TASK_NAMES) => {
          const getRandomTime = () => {
            const hour = Math.floor(Math.random() * 12) + 1;
            const minutes = ["", ":00", ":15", ":30", ":45"][
              Math.floor(Math.random() * 5)
            ];
            const ampm = Math.random() > 0.5 ? "a" : "p";
            return `${hour}${minutes}${ampm}`;
          };

          let weekRows = document.querySelectorAll(
            ".fc-content-skeleton tbody tr"
          );
          weekRows = Array.from(weekRows).slice(0, -3);
          let totalAdded = 0; // Total events added
          const toBeAdded = 25; // Total events to be added

          // Max number of events per day
          const MAX_EVENTS_PER_DAY = 4;

          // Create an array for the days (21 days) that holds the number of events
          let daysEventsMap = Array(21).fill(0); // Using let here instead of const

          // Randomly distribute events such that the sum of the events equals 25
          while (daysEventsMap.reduce((acc, val) => acc + val, 0) < toBeAdded) {
            let randomIndex = Math.floor(Math.random() * 21); // Random day index (0-20)
            if (daysEventsMap[randomIndex] < MAX_EVENTS_PER_DAY) {
              daysEventsMap[randomIndex]++;
            }
          }

          // Ensure we exactly have 25 events (if there's an issue where it's slightly under, we can fill it)
          const totalEvents = daysEventsMap.reduce((acc, val) => acc + val, 0);
          if (totalEvents < toBeAdded) {
            let remainingEvents = toBeAdded - totalEvents;
            for (
              let i = 0;
              remainingEvents > 0 && i < daysEventsMap.length;
              i++
            ) {
              if (daysEventsMap[i] < MAX_EVENTS_PER_DAY) {
                daysEventsMap[i]++;
                remainingEvents--;
              }
            }
          }

          // Now `daysEventsMap` contains the number of events for each of the 21 days

          // Add events to the calendar
          let dayIndex = 0;
          weekRows.forEach((row, rowIndex) => {
            const dayCells = row.querySelectorAll("td");

            dayCells.forEach((td, index) => {
              const numEventsForDay = daysEventsMap[dayIndex];

              // If we have events for this day
              for (let j = 0; j < numEventsForDay; j++) {
                const color = COLORS[Math.floor(Math.random() * COLORS.length)];
                const task =
                  TASK_NAMES[Math.floor(Math.random() * TASK_NAMES.length)];
                const timeStr = getRandomTime();

                const a = document.createElement("a");
                a.className =
                  "fc-day-grid-event fc-h-event fc-event fc-start fc-end event";
                a.title = `${task}`;
                a.style.borderColor = color;
                a.style.color = color;

                const content = document.createElement("div");
                content.className = "fc-content";

                const icon = document.createElement("i");
                icon.className = "icon-note-light";

                const time = document.createElement("span");
                time.className = "fc-time";
                time.innerText = timeStr;

                const titleWrapper = document.createElement("span");
                titleWrapper.className = "fc-title";

                const titleText = document.createTextNode(`${task}`);
                titleWrapper.appendChild(titleText);

                a.setAttribute("data-day-of-week", index); // 0 is Sunday, 1 is Monday, etc.
                content.appendChild(icon);
                content.appendChild(time);
                content.appendChild(titleWrapper);
                a.appendChild(content);

                td.appendChild(a);
                totalAdded++;
              }
              dayIndex++;
            });
          });
        },
        COLORS,
        TASK_NAMES
      );

      const boxes = await page.evaluate(() => {
        return Array.from(document.querySelectorAll(".event")).map((el) => {
          const rect = el.getBoundingClientRect();
          const dayOfWeek = parseInt(el.getAttribute("data-day-of-week"), 10);
          const headerCells = document.querySelectorAll("thead .fc-day-top");
          const dayCell = headerCells[dayOfWeek];
          const date = dayCell
            ? dayCell.getAttribute("data-date")
            : "Invalid Date";

          const timeText = el.querySelector(".fc-time")
            ? el.querySelector(".fc-time").textContent
            : "";
          const assignment = el.querySelector(".fc-title")
            ? el.querySelector(".fc-title").textContent
            : "";

          const weekday = [
            "Sunday",
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
          ][dayOfWeek];

          const dayNumber = date.split("-")[2];

          return {
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            weekday: weekday,
            date: dayNumber,
            time: timeText,
            task: assignment,
          };
        });
      });

      const imgWidth = 800;
      const imgHeight = 600;

      const builder = new xml2js.Builder();
      const annotation = {
        annotation: {
          folder: "images",
          filename: `calendar_${i}.jpg`, // Save as JPG
          path: path.join(labelDir, `calendar_${i}.jpg`),
          size: {
            width: imgWidth,
            height: imgHeight,
            depth: 3,
          },
          object: boxes.map((b) => ({
            name: b.task,
            pose: "Unspecified",
            truncated: 0,
            difficult: 0,
            bndbox: {
              xmin: Math.floor(b.x),
              ymin: Math.floor(b.y),
              xmax: Math.floor(b.x + b.width),
              ymax: Math.floor(b.y + b.height),
            },
          })),
        },
      };

      const xml = builder.buildObject(annotation);
      const labelPath = path.join(labelDir, `calendar_${i}.xml`);
      fs.writeFileSync(labelPath, xml);

      const tempImagePath = path.join(tempDir, `calendar_${i}.png`); // Temp folder path

      // Save the screenshot as a PNG file in the temp folder
      await page.screenshot({ path: tempImagePath, type: "png" });

      // Resize the image to 800x600 and save it as JPG in the imgDir (without cropping)
      const finalImgPath = path.join(imgDir, `calendar_${i}.jpg`);
      await sharp(tempImagePath)
        // .resize(800, 450) // Resize to the target size (800x600)
        .toFormat("jpeg") // Save as JPG
        .toFile(finalImgPath); // Save to final location

      // Clean up by removing the temporary PNG file
      fs.unlinkSync(tempImagePath);

      console.log(`Generated and resized ${finalImgPath} and ${labelPath}`);
      await page.close();
    };

    pagePromises.push(pagePromise());
  }

  await Promise.all(pagePromises);
  await browser.close(); // ✅ Only close once after all tasks are finished
})();
