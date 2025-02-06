const DashboardLayout = ({ children }) => {
  return (
    <div className="grid grid-cols-[repeat(2,1fr)] grid-rows-[repeat(2,1fr)] gap-y-[5px] gap-x-[5px]">
      <div className="row-1 row-2 col-1 col-2">1</div>
      <div className="row-1 row-2 col-2 col-3">2</div>
      <div className="row-2 row-3 col-1 col-2">3</div>
      <div className="row-2 row-3 col-2 col-3">4</div>
    </div>
  );
};

export default DashboardLayout;
