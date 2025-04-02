import { useState, useEffect } from "react";

import logoDark from "@/assets/logo-dark.png";
import logoLight from "@/assets/logo-light.png";

import { useTheme } from "../hooks/use-theme";

type LogoProps = {
  className?: string;
};

const Logo = ({ className }: LogoProps) => {
  const { theme } = useTheme();
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    const checkDarkMode = () => {
      switch (theme) {
        case "dark":
          setIsDarkMode(true);
          break;
        case "light":
          setIsDarkMode(false);
          break;
        default: // theme == system
          setIsDarkMode(window.matchMedia("(prefers-color-scheme: dark)").matches);
          break;
      }
    };

    checkDarkMode();

    // For system theme, listen to changes in color scheme preference
    if (theme === "system") {
      const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
      const handleChange = () => checkDarkMode();

      mediaQuery.addEventListener("change", handleChange);
      return () => mediaQuery.removeEventListener("change", handleChange);
    }
  }, [theme]);

  // Determine which logo to display based on dark mode status
  const logoSrc = isDarkMode ? logoLight : logoDark;

  return (
    <img
      src={logoSrc}
      className={className}
      alt="Sentix Logo"
    />
  );
};

export default Logo;
