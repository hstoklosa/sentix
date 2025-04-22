import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

type ErrorMessageProps = {
  message: string;
  className?: string;
};

const ErrorMessage = ({ message, className }: ErrorMessageProps) => {
  return (
    <div className={cn("flex items-center gap-2 text-destructive", className)}>
      <AlertCircle className="size-4" />
      <span>{message}</span>
    </div>
  );
};

export default ErrorMessage;
