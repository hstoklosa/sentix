import defaultTheme from 'tailwindcss/defaultTheme.js';
import plugin from "tailwindcss/plugin";
import animate from "tailwindcss-animate";

/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    plugins: [animate],
}