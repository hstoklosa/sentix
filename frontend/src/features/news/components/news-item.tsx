import { NewsItem as NewsItemType } from "@/features/news/types";

type NewsItemProps = {
  news: NewsItemType;
};

const NewsItem = ({ news }: NewsItemProps) => {
  return (
    <div className="border-b border-border pb-4">
      <h3 className="font-medium">{news.title}</h3>
      <p className="text-sm text-muted-foreground">{news.body}</p>
    </div>
  );
};

export default NewsItem;
