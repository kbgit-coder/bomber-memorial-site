import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';

const storiesDir = path.join(process.cwd(), 'public/data/stories');

export interface Story {
  slug: string;
  title: string;
  subtitle?: string;
  author: string;
  date: string;
  memorial_slugs: string[];
  summary: string;
  tags: string[];
  contentHtml: string;
}

export interface StoryMeta {
  slug: string;
  title: string;
  subtitle?: string;
  author: string;
  date: string;
  memorial_slugs: string[];
  summary: string;
  tags: string[];
}

function parseStoryFile(fileName: string): StoryMeta {
  const slug = fileName.replace(/\.md$/, '');
  const filePath = path.join(storiesDir, fileName);
  const fileContents = fs.readFileSync(filePath, 'utf8');
  const { data } = matter(fileContents);

  return {
    slug,
    title: data.title || slug,
    subtitle: data.subtitle,
    author: data.author || 'Unknown',
    date: data.date || '',
    memorial_slugs: data.memorial_slugs || [],
    summary: data.summary || '',
    tags: data.tags || [],
  };
}

export function getAllStories(): StoryMeta[] {
  if (!fs.existsSync(storiesDir)) return [];
  const fileNames = fs.readdirSync(storiesDir).filter((f) => f.endsWith('.md'));
  return fileNames
    .map(parseStoryFile)
    .sort((a, b) => b.date.localeCompare(a.date));
}

export function getAllStorySlugs(): string[] {
  if (!fs.existsSync(storiesDir)) return [];
  return fs
    .readdirSync(storiesDir)
    .filter((f) => f.endsWith('.md'))
    .map((f) => f.replace(/\.md$/, ''));
}

export async function getStoryBySlug(slug: string): Promise<Story | undefined> {
  const filePath = path.join(storiesDir, `${slug}.md`);
  if (!fs.existsSync(filePath)) return undefined;

  const fileContents = fs.readFileSync(filePath, 'utf8');
  const { data, content } = matter(fileContents);

  const processed = await remark().use(html).process(content);
  const contentHtml = processed.toString();

  return {
    slug,
    title: data.title || slug,
    subtitle: data.subtitle,
    author: data.author || 'Unknown',
    date: data.date || '',
    memorial_slugs: data.memorial_slugs || [],
    summary: data.summary || '',
    tags: data.tags || [],
    contentHtml,
  };
}

export function getStoriesForMemorial(memorialSlug: string): StoryMeta[] {
  return getAllStories().filter((s) => s.memorial_slugs.includes(memorialSlug));
}
