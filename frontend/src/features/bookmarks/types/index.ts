export interface BookmarkCreate {
  news_item_id: number;
}

export interface BookmarkResponse {
  id: number;
  user_id: number;
  news_item_id: number;
  created_at: string;
}
