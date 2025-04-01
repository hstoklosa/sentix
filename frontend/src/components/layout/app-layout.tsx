const AppLayout = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="container mx-auto">
      <header>
        <h1>Dashboard</h1>
      </header>

      <main>{children}</main>
    </div>
  );
};

export default AppLayout;
