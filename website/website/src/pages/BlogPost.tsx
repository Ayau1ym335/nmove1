import { Navbar } from "@/components/Navbar";
import { Footer } from "@/components/Footer";
import { useParams, Link, Navigate } from "react-router-dom";
import { blogPosts } from "@/data/blogPosts";
import { Calendar, Clock, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

// Simple markdown renderer (basic)
function renderMarkdown(content: string) {
    // Split by lines and process
    const lines = content.trim().split("\n");
    const elements: JSX.Element[] = [];
    let currentList: string[] = [];
    let listType: "ul" | "ol" | null = null;

    const flushList = () => {
        if (currentList.length > 0 && listType) {
            const ListTag = listType;
            elements.push(
                <ListTag key={elements.length} className={listType === "ul" ? "list-disc pl-6 space-y-2 my-4" : "list-decimal pl-6 space-y-2 my-4"}>
                    {currentList.map((item, i) => (
                        <li key={i} className="text-muted-foreground">{item}</li>
                    ))}
                </ListTag>
            );
            currentList = [];
            listType = null;
        }
    };

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Headers
        if (line.startsWith("# ")) {
            flushList();
            elements.push(<h1 key={i} className="text-3xl font-bold mt-8 mb-4">{line.slice(2)}</h1>);
        } else if (line.startsWith("## ")) {
            flushList();
            elements.push(<h2 key={i} className="text-2xl font-semibold mt-8 mb-4">{line.slice(3)}</h2>);
        } else if (line.startsWith("### ")) {
            flushList();
            elements.push(<h3 key={i} className="text-xl font-semibold mt-6 mb-3">{line.slice(4)}</h3>);
        }
        // Horizontal rule
        else if (line.startsWith("---")) {
            flushList();
            elements.push(<hr key={i} className="my-8 border-border" />);
        }
        // Unordered list
        else if (line.startsWith("- ")) {
            if (listType !== "ul") {
                flushList();
                listType = "ul";
            }
            currentList.push(line.slice(2));
        }
        // Numbered list
        else if (/^\d+\. /.test(line)) {
            if (listType !== "ol") {
                flushList();
                listType = "ol";
            }
            currentList.push(line.replace(/^\d+\. /, ""));
        }
        // Bold text in paragraphs
        else if (line.trim()) {
            flushList();
            // Replace **text** with bold
            const processed = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-foreground">$1</strong>');
            // Replace *text* with italic
            const processed2 = processed.replace(/\*(.*?)\*/g, '<em>$1</em>');
            // Replace [text](link) with links
            const processed3 = processed2.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-primary hover:underline">$1</a>');

            elements.push(
                <p
                    key={i}
                    className="text-muted-foreground leading-relaxed my-4"
                    dangerouslySetInnerHTML={{ __html: processed3 }}
                />
            );
        }
    }

    flushList();
    return elements;
}

const BlogPost = () => {
    const { slug } = useParams<{ slug: string }>();
    const post = blogPosts.find((p) => p.slug === slug);

    if (!post) {
        return <Navigate to="/blog" replace />;
    }

    return (
        <div className="min-h-screen bg-background">
            <Navbar />

            <article className="pt-32 pb-16">
                <div className="container mx-auto px-6">
                    <div className="max-w-3xl mx-auto">
                        {/* Back link */}
                        <Link to="/blog" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-8">
                            <ArrowLeft className="h-4 w-4" />
                            Back to Blog
                        </Link>

                        {/* Header */}
                        <header className="mb-12">
                            <span className="inline-block px-3 py-1 rounded-full bg-primary/10 text-primary text-sm font-medium mb-4">
                                {post.category}
                            </span>

                            <h1 className="text-4xl md:text-5xl font-semibold mb-6">
                                {post.title}
                            </h1>

                            <div className="flex items-center gap-6 text-sm text-muted-foreground">
                                <span className="flex items-center gap-2">
                                    <Calendar className="h-4 w-4" />
                                    {new Date(post.date).toLocaleDateString("en-US", {
                                        month: "long",
                                        day: "numeric",
                                        year: "numeric",
                                    })}
                                </span>
                                <span className="flex items-center gap-2">
                                    <Clock className="h-4 w-4" />
                                    {post.readTime}
                                </span>
                            </div>
                        </header>

                        {/* Content */}
                        <div className="prose prose-invert max-w-none">
                            {renderMarkdown(post.content)}
                        </div>

                        {/* Footer CTA */}
                        <div className="mt-16 p-8 rounded-2xl bg-card border border-border text-center">
                            <h3 className="text-xl font-semibold mb-3">Track your movement journey</h3>
                            <p className="text-muted-foreground mb-6">
                                Join our waitlist to be among the first to try NMove.
                            </p>
                            <Link to="/contact">
                                <Button className="bg-primary text-primary-foreground hover:bg-primary/90">
                                    Join Waitlist
                                </Button>
                            </Link>
                        </div>
                    </div>
                </div>
            </article>

            <Footer />
        </div>
    );
};

export default BlogPost;
