// Blog post data - can be moved to a separate file or fetched from backend
export interface BlogPost {
    slug: string;
    title: string;
    excerpt: string;
    date: string;
    readTime: string;
    category: string;
    content: string;
}


export const blogPosts: BlogPost[] = [
    {
        slug: "coming-soon",
        title: "Coming Soon",
        excerpt: "We are currently working on meaningful content for our readers. Please check back soon.",
        date: "2026-02-01",
        readTime: "1 min read",
        category: "Updates",
        content: `
# Blog Coming Soon

We are busy writing articles to help you understand your movement health better. 

Stay tuned for updates!
`
    }
];
