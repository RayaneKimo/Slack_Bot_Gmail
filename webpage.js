// render.js
const puppeteer = require('puppeteer');
const fs = require('fs');

const htmlContent = process.argv[2]; // The second argument is the HTML content


(async () => {
    // Launch a headless browser
    const browser = await puppeteer.launch();
    const page = await browser.newPage();

    // Set the HTML content
    await page.setContent(htmlContent, {
        waitUntil: 'networkidle0' // Wait for the page to fully load
    });

    // Take a screenshot
    await page.screenshot({
        path: 'screenshot.png', // Save the screenshot as an image
        fullPage: true // Capture the entire page
    });

    // Close the browser
    await browser.close();

    console.log('Screenshot saved as screenshot.png');
})();