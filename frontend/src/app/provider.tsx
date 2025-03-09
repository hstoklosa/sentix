const AppProvider = ({ children }: { children: React.ReactNode }) => {
  return (
    <>
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
    </>
  );
};

export default AppProvider;
