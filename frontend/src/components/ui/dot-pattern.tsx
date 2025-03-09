export const DotPattern = () => {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <div
        className="absolute inset-0 bg-dots-pattern"
        style={{
          maskImage:
            "radial-gradient(circle at center, transparent 25%, rgba(0, 0, 0, 0.7) 50%, black 75%)",
          WebkitMaskImage:
            "radial-gradient(circle at center, transparent 25%, rgba(0, 0, 0, 0.7) 50%, black 75%)",
        }}
      />
    </div>
  );
};
