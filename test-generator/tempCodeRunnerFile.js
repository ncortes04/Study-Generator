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