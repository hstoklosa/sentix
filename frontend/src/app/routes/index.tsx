import { useEffect, useMemo, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { MoveRight, BarChart3 } from "lucide-react";

import { Button, DotPattern } from "@/components/ui";

const Landing = () => {
  const [titleIndex, setTitleIndex] = useState(0);
  const titles = useMemo(() => ["powerful", "accurate", "real-time"], []);

  useEffect(() => {
    const intervalId = setInterval(() => {
      setTitleIndex((prevIndex) =>
        prevIndex === titles.length - 1 ? 0 : prevIndex + 1
      );
    }, 2000);

    return () => clearInterval(intervalId);
  }, [titles.length]);

  return (
    <div className="relative min-h-screen w-full flex items-center justify-center">
      <DotPattern />

      <div className="container flex flex-col items-center justify-center gap-6 py-20">
        {/* <div>
          <Button
            variant="secondary"
            size="sm"
            className="gap-4"
          >
            Explore our API docs <MoveRight className="w-4 h-4" />
          </Button>
        </div> */}

        <div className="flex gap-4 flex-col">
          <h1 className="text-5xl md:text-7xl max-w-2xl tracking-tighter text-center font-normal">
            <span className="text-primary">Trade smarter with</span>
            <div className="flex justify-center items-center space-x-4">
              <div className="relative inline-flex">
                <span className="invisible whitespace-nowrap">
                  {titles.reduce((a, b) => (a.length > b.length ? a : b))}
                </span>
                {titles.map((title, index) => (
                  <span
                    key={index}
                    className={`absolute inset-0 font-semibold whitespace-nowrap transition-all duration-500 ease-in-out ${
                      titleIndex === index
                        ? "opacity-100 translate-y-0"
                        : titleIndex > index
                          ? "opacity-0 -translate-y-16"
                          : "opacity-0 translate-y-16"
                    }`}
                  >
                    {title}
                  </span>
                ))}
              </div>
              <span>&nbsp;insights</span>
            </div>
          </h1>

          <p className="text-lg md:text-xl leading-relaxed tracking-tight text-muted-foreground max-w-2xl text-center">
            Navigate cryptocurrency markets with confidence using SentiX's real-time
            sentiment analysis that delivers precise insights that help you spot
            opportunities and minimize risks before others do.
          </p>
        </div>
        <div className="flex flex-row gap-3">
          <Button
            size="lg"
            className="gap-4"
            variant="outline"
            asChild
          >
            <Link to="/dashboard">
              View dashboard <BarChart3 className="w-4 h-4" />
            </Link>
          </Button>
          <Button
            size="lg"
            className="gap-4"
            asChild
          >
            <Link to="/register">
              Get started
              <MoveRight className="w-4 h-4" />
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
};

export const Route = createFileRoute("/")({
  component: Landing,
  head: () => ({
    meta: [{ title: "Sentix | Real-Time Insights for Crypto Markets" }],
  }),
});
