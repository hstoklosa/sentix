import { Sun, Moon, TvMinimal } from "lucide-react";

import { useTheme } from "@/hooks/use-theme";
import { ToggleGroup, ToggleGroupItem } from "./ui/toggle-group";

const ThemeToggle = () => {
  const { theme, setTheme } = useTheme();

  return (
    <ToggleGroup
      type="single"
      variant="outline"
      size="sm"
      value={theme}
      onValueChange={setTheme}
    >
      <ToggleGroupItem
        value="light"
        aria-label="Light mode"
        className="px-2"
      >
        <Sun className="size-3.5" />
      </ToggleGroupItem>
      <ToggleGroupItem
        value="dark"
        aria-label="Dark mode"
        className="px-2"
      >
        <Moon className="size-3.5" />
      </ToggleGroupItem>
      <ToggleGroupItem
        value="system"
        aria-label="System mode"
        className="px-2"
      >
        <TvMinimal className="size-3.5" />
      </ToggleGroupItem>
    </ToggleGroup>
  );
};

export default ThemeToggle;
