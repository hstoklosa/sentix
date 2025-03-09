export const DotPattern = () => {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <div
        className="absolute inset-0 bg-dots-pattern"
        style={{
          maskImage:
            "radial-gradient(ellipse 90% 70% at center, transparent 5%, rgba(0, 0, 0, 0.5) 20%, rgba(0, 0, 0, 0.8) 40%, black 60%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 90% 70% at center, transparent 5%, rgba(0, 0, 0, 0.5) 20%, rgba(0, 0, 0, 0.8) 40%, black 60%)",
        }}
      />
    </div>
  );
};
