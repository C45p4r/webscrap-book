# Web Scraping Project: Book Chapters

## Project Overview

This project scrapes chapters from a book website and saves them to text files.

- **Example Book:** [OVERLORD - First Chapter](https://www.bilibili.com/opus/763979363954720774?spm_id_from=333.1387.0.0)

The program will:

- Open the site using chrome browser
- Scrape the chapters of the book
- Save each chapter to a text file

## CSS Selectors to Focus On

- **Book title:** `.opus-module-title__text`
- **Book content (chapter):** `.opus-module-content`
- **Chapter menu:** `.opus-collection__content`
- **Next chapter button:** The next `.opus-collection__item` after `.opus-collection__item.active`

## Requirements

- Python 3.x
- Selenium
- WebDriver for your browser (e.g., ChromeDriver for Chrome)

## Output

A `.txt` file will be created for each chapter, saved as `/OVERLORD/chapter_x<chapter_number>.txt`.
