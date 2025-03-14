import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const spinnerVariants = cva("animate-spin rounded-full border-solid", {
  variants: {
    variant: {
      primary: "border-primary/20 border-t-primary",
      secondary: "border-secondary/20 border-t-secondary",
      tertiary: "border-tertiary/20 border-t-tertiary",
      white: "border-white/20 border-t-white",
    },
    size: {
      sm: "h-4 w-4 border-2",
      md: "h-8 w-8 border-[3px]",
      lg: "h-16 w-16 border-4",
      xl: "h-24 w-24 border-[6px]",
    },
  },
  defaultVariants: {
    variant: "primary",
    size: "md",
  },
});

type SpinnerProps = {
  className?: string;
  fullScreen?: boolean;
} & VariantProps<typeof spinnerVariants>;

const Spinner = ({
  className,
  fullScreen = false,
  size = "md",
  variant = "primary",
}: SpinnerProps) => {
  return (
    <div
      className={cn(
        "flex items-center justify-center",
        fullScreen && "h-screen w-full",
        className
      )}
    >
      <div className={cn(spinnerVariants({ variant, size }))} />
    </div>
  );
};

export { Spinner };
