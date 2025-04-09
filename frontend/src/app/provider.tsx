import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createQueryClient } from "@/lib/react-query";
import { ThemeProvider } from "@/hooks/use-theme";
import { TokenPriceProvider } from "@/features/coins/context/token-price-context";

const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();

  return (
    <ThemeProvider>
      <QueryClientProvider client={queryClient}>
        <TokenPriceProvider>
          <ReactQueryDevtools
            initialIsOpen={false}
            buttonPosition="bottom-right"
          />
          {children}
        </TokenPriceProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default AppProvider;
