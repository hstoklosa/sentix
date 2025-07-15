import { NewsItem } from "@/features/news/types";

export interface BookmarkCreate {
  post_id: number;
}

export interface BookmarkResponse {
  id: number;
  user_id: number;
  post_id: number;
  created_at: string;
}

export interface BookmarkStatus {
  is_bookmarked: boolean;
}

export interface BookmarkedNewsItem extends NewsItem {
  bookmark_id: number;
  bookmarked_at: string;
}

export interface BookmarkedNewsResponse {
  items: BookmarkedNewsItem[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}
