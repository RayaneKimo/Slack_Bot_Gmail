const puppeteer = require('puppeteer');

const htmlContent = process.argv[2]; // The second argument is the HTML content

(async () => {
    // Launch a headless browser
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Set the HTML content
    await page.setContent(htmlContent, {
        waitUntil: 'networkidle0' // Wait for the page to fully load
    });

    // Evaluate the bounding box of the content
    const clip = await page.evaluate(() => {
        const content = document.body.querySelector('*'); // Capture the first visible element
        if (!content) {
            throw new Error('No content found on the page!');
        }
        const { x, y, width, height } = content.getBoundingClientRect();
        const padding = 20; // Add padding (in pixels) to all sides

        return {
            x: Math.max(0, x - padding), // Prevent negative x
            y: Math.max(0, y - padding), // Prevent negative y
            width: width + 2 * padding,
            height: height + 2 * padding
        };
    });

    // Take a screenshot of the content only
    await page.screenshot({
        path: 'screenshot.png', // Save the screenshot as an image
        clip: clip // Capture only the content's bounding box with padding
    });

    // Close the browser
    await browser.close();

    console.log('Screenshot saved as screenshot.png');
})();
