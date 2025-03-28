const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

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
const labelDir = path.join(outputDir, "labels");

if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);
if (!fs.existsSync(imgDir)) fs.mkdirSync(imgDir);
if (!fs.existsSync(labelDir)) fs.mkdirSync(labelDir);

const TOTAL_IMAGES = 1000;

(async () => {
  const browser = await puppeteer.launch({
    headless: "new",
  });
  // Create an array of promises for processing each page
  const pagePromises = [];

  for (let i = 900; i < TOTAL_IMAGES; i++) {
    const pagePromise = async () => {
      const page = await browser.newPage();
      const htmlPath = path.resolve(__dirname, "canvas-calendar.html");
      await page.goto("file://" + htmlPath, { waitUntil: "domcontentloaded" });
      // page.on("console", (msg) => {
      //   console.log("PAGE LOG:", msg.text()); // Logs the message in the console
      // });
      await page.setViewport({ width: 1200, height: 1100 });
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

          const weekRows = document.querySelectorAll(
            ".fc-content-skeleton tbody tr"
          );

          weekRows.forEach((row) => {
            const dayCells = row.querySelectorAll("td");

            dayCells.forEach((td, index) => {
              if (!td.classList.contains("fc-event-container")) {
                td.classList.add("fc-event-container");
              }

              const numEvents = Math.floor(Math.random() * 4);
              for (let j = 0; j < numEvents; j++) {
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
              }
            });
          });
        },
        COLORS,
        TASK_NAMES // Just pass these as arguments
      );

      const boxes = await page.evaluate(() => {
        return Array.from(document.querySelectorAll(".event")).map((el) => {
          const rect = el.getBoundingClientRect(); // Get the event's position and dimensions
          const dayOfWeek = parseInt(el.getAttribute("data-day-of-week"), 10); // Get the index for the day (0 for Sunday, etc.)
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
          ][dayOfWeek]; // Get the weekday (Sunday, Monday, etc.)

          const dayNumber = date.split("-")[2]; // Extract the day number

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

      const imgWidth = 1200;
      const imgHeight = 1100;

      const yoloLabels = boxes.map((b) => {
        const cx = (b.x + b.width / 2) / imgWidth;
        const cy = (b.y + b.height / 2) / imgHeight;
        const w = b.width / imgWidth;
        const h = b.height / imgHeight;

        return `${b.weekday}, ${b.date}, ${b.time}, ${b.task}, ${cx.toFixed(
          6
        )} ${cy.toFixed(6)} ${w.toFixed(6)} ${h.toFixed(6)}`;
      });

      const imgPath = path.join(imgDir, `calendar_${i}.png`);
      const labelPath = path.join(labelDir, `calendar_${i}.txt`);

      await page.screenshot({ path: imgPath });
      fs.writeFileSync(labelPath, yoloLabels.join("\n"));

      await page.close();
      console.log(`Generated ${imgPath} and ${labelPath}`);
    };

    // Push each page task as a promise
    pagePromises.push(pagePromise());
  }

  await Promise.all(pagePromises);

  await browser.close(); // ✅ Only close once after all tasks are finished
})();
