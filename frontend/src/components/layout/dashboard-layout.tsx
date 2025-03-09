const DashboardLayout = () => {
  return (
    <div className="grid grid-cols-[repeat(3,1fr)] grid-rows-[repeat(3,1fr)] gap-x-2 gap-y-2">
      <div className="row-start-1 row-end-4 col-start-1 col-end-2">1</div>

      <div className="row-start-1 row-end-2 col-start-2 col-end-4">2</div>

      <div className="row-start-2 row-end-4 col-start-2 col-end-3">3</div>

      <div className="row-start-2 row-end-4 col-start-3 col-end-4">4</div>
    </div>
  );
};

export default DashboardLayout;
