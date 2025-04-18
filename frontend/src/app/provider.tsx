import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";

import { createQueryClient } from "@/lib/react-query";
import { WebSocketProvider } from "@/features/news/context";

import { Toaster } from "@/components/ui/sonner";
import { ThemeProvider } from "@/hooks/use-theme";

const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();

  return (
    <ThemeProvider>
      <Toaster richColors={true} />
      <QueryClientProvider client={queryClient}>
        <ReactQueryDevtools
          initialIsOpen={false}
          buttonPosition="bottom-right"
        />
        {/* WebSocketProvider is now a child component to ensure hooks work */}
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default AppProvider;
