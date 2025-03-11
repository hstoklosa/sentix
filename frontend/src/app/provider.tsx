import { QueryClientProvider } from "@tanstack/react-query";
import { createQueryClient } from "@/lib/react-query";

const AppProvider = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      {/* TODO: Fix TanStack devtools preventing the app from rendering
      {import.meta.env.DEV && (
        <>
          <ReactQueryDevtools
            buttonPosition="top-right"
            initialIsOpen={false}
          />
          <TanStackRouterDevtools
            position="bottom-right"
            initialIsOpen={false}
          />
        </>
      )} */}
      {children}
    </QueryClientProvider>
  );
};

export default AppProvider;
