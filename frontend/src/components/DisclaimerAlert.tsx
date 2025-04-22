import { useEffect, useState } from "react";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { useLocalStorage } from "@/hooks/use-local-storage";

export function DisclaimerAlert() {
  const [open, setOpen] = useState(false);
  const [hasAcknowledged, setHasAcknowledged] = useLocalStorage(
    "disclaimer-acknowledged",
    false
  );

  useEffect(() => {
    if (!hasAcknowledged) {
      setOpen(true);
    }
  }, [hasAcknowledged]);

  const handleAcknowledge = () => {
    setHasAcknowledged(true);
    setOpen(false);
  };

  return (
    <AlertDialog
      open={open}
      onOpenChange={setOpen}
    >
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Important Disclaimer</AlertDialogTitle>
          <AlertDialogDescription>
            <p className="mb-2">
              The information provided by Sentix is for informational purposes only
              and does not constitute financial advice.
            </p>
            <p className="mb-2">
              Cryptocurrency investments are volatile and high-risk. The sentiment
              analysis and data provided by this application should not be the sole
              basis for any investment decisions.
            </p>
            <p className="mb-2">
              You are solely responsible for evaluating the risks and merits of any
              cryptocurrency-related decisions. Past performance is not indicative
              of future results.
            </p>
            <p>
              By using Sentix, you acknowledge that you understand these risks and
              are solely responsible for your investment decisions.
            </p>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogAction onClick={handleAcknowledge}>
            I Understand and Accept
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
