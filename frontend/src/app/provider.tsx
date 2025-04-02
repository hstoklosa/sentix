import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createQueryClient } from "@/lib/react-query";
import { ThemeProvider } from "@/hooks/use-theme";

const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <ReactQueryDevtools
          buttonPosition="top-right"
          initialIsOpen={false}
        />
        {children}
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default AppProvider;
