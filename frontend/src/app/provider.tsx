import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { createQueryClient } from "@/lib/react-query";

const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools
        buttonPosition="top-right"
        initialIsOpen={false}
      />
      {children}
    </QueryClientProvider>
  );
};

export default AppProvider;
