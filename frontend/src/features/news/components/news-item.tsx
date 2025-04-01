import React from "react";
import { NewsItem as NewsItemType } from "../types";

interface NewsItemProps {
  news: NewsItemType;
  isHighlighted?: boolean;
}

export const NewsItem: React.FC<NewsItemProps> = ({
  news,
  isHighlighted = false,
}) => {
  const formattedDate = new Date(news.time).toLocaleString();

  return (
    <div
      className={`p-4 mb-4 rounded-lg shadow-md transition-all duration-300 ${
        isHighlighted
          ? "bg-blue-50 border-l-4 border-blue-500 animate-pulse"
          : "bg-white"
      }`}
    >
      <div className="flex items-start">
        {news.icon && (
          <img
            src={news.icon}
            alt={`${news.source} icon`}
            className="w-8 h-8 mt-1 mr-3"
            onError={(e) => {
              // Replace broken image with fallback
              (e.target as HTMLImageElement).src = "https://via.placeholder.com/32";
            }}
          />
        )}

        <div className="flex-1">
          <div className="flex justify-between items-start mb-2">
            <h3 className="text-lg font-semibold text-gray-800 hover:text-blue-600">
              {news.url ? (
                <a
                  href={news.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline"
                >
                  {news.title}
                </a>
              ) : (
                news.title
              )}
            </h3>
          </div>

          <p className="text-gray-600 mb-3 line-clamp-3">{news.body}</p>

          <div className="flex flex-wrap justify-between items-center text-sm">
            <div className="flex items-center text-gray-500">
              <span className="mr-2">{news.source}</span>
              <span>{formattedDate}</span>
            </div>

            {news.coins && news.coins.length > 0 && (
              <div className="flex flex-wrap mt-2 sm:mt-0">
                {news.coins.map((coin: string) => (
                  <span
                    key={coin}
                    className="inline-block bg-gray-100 rounded-full px-3 py-1 text-xs font-semibold text-gray-700 mr-2 mb-1"
                  >
                    {coin}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {news.image && (
        <div className="mt-3">
          <img
            src={news.image}
            alt={news.title}
            className="w-full h-48 object-cover rounded"
            onError={(e) => {
              // Remove broken image element
              (e.target as HTMLImageElement).style.display = "none";
            }}
          />
        </div>
      )}
    </div>
  );
};
