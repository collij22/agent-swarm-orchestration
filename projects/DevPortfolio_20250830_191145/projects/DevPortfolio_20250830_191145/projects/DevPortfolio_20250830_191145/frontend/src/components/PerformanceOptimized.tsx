/**
 * Performance-Optimized React Components
 * Implements lazy loading, memoization, and efficient rendering
 */

import React, { memo, lazy, Suspense, useCallback, useMemo } from 'react'
import { useIntersectionObserver } from '@/hooks/useIntersectionObserver'
import { useImagePreloader } from '@/hooks/useImagePreloader'

// Lazy load heavy components
const BlogEditor = lazy(() => import('./BlogEditor'))
const ProjectGallery = lazy(() => import('./ProjectGallery'))
const AnalyticsChart = lazy(() => import('./AnalyticsChart'))
const SkillsVisualization = lazy(() => import('./SkillsVisualization'))

// Loading skeleton components
const LoadingSkeleton = memo(({ height = 200, className = '' }: { height?: number; className?: string }) => (
  <div 
    className={`animate-pulse bg-gray-200 rounded-lg ${className}`}
    style={{ height: `${height}px` }}
    aria-label="Loading content"
  />
))

// Optimized image component with lazy loading
interface OptimizedImageProps {
  src: string
  alt: string
  className?: string
  width?: number
  height?: number
  priority?: boolean
  placeholder?: string
}

export const OptimizedImage = memo<OptimizedImageProps>(({
  src,
  alt,
  className = '',
  width,
  height,
  priority = false,
  placeholder = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjE4IiBmaWxsPSIjYWFhIiBkeT0iLjNlbSIgdGV4dC1hbmNob3I9Im1pZGRsZSI+TG9hZGluZy4uLjwvdGV4dD48L3N2Zz4='
}) => {
  const [ref, isVisible] = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '50px',
  })
  
  const { isLoaded, error } = useImagePreloader(isVisible || priority ? src : null)
  
  return (
    <div ref={ref} className={`relative overflow-hidden ${className}`}>
      <img
        src={isLoaded ? src : placeholder}
        alt={alt}
        width={width}
        height={height}
        className={`transition-opacity duration-300 ${
          isLoaded ? 'opacity-100' : 'opacity-0'
        }`}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
      />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <span className="text-gray-500 text-sm">Failed to load image</span>
        </div>
      )}
    </div>
  )
})

// Virtualized list for large datasets
interface VirtualizedListProps<T> {
  items: T[]
  itemHeight: number
  containerHeight: number
  renderItem: (item: T, index: number) => React.ReactNode
  className?: string
}

export const VirtualizedList = memo(<T extends any>({
  items,
  itemHeight,
  containerHeight,
  renderItem,
  className = ''
}: VirtualizedListProps<T>) => {
  const [scrollTop, setScrollTop] = React.useState(0)
  
  const visibleItems = useMemo(() => {
    const startIndex = Math.floor(scrollTop / itemHeight)
    const endIndex = Math.min(
      startIndex + Math.ceil(containerHeight / itemHeight) + 1,
      items.length
    )
    
    return items.slice(startIndex, endIndex).map((item, index) => ({
      item,
      index: startIndex + index,
    }))
  }, [items, itemHeight, containerHeight, scrollTop])
  
  const handleScroll = useCallback((e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop)
  }, [])
  
  return (
    <div
      className={`overflow-auto ${className}`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      <div style={{ height: items.length * itemHeight, position: 'relative' }}>
        {visibleItems.map(({ item, index }) => (
          <div
            key={index}
            style={{
              position: 'absolute',
              top: index * itemHeight,
              height: itemHeight,
              width: '100%',
            }}
          >
            {renderItem(item, index)}
          </div>
        ))}
      </div>
    </div>
  )
})

// Memoized blog post card
interface BlogPostCardProps {
  post: {
    id: string
    title: string
    excerpt: string
    slug: string
    publishedAt: string
    tags: string[]
    readTime: number
    featured: boolean
  }
  onClick?: (slug: string) => void
}

export const BlogPostCard = memo<BlogPostCardProps>(({ post, onClick }) => {
  const handleClick = useCallback(() => {
    onClick?.(post.slug)
  }, [onClick, post.slug])
  
  return (
    <article 
      className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow cursor-pointer"
      onClick={handleClick}
    >
      <div className="flex items-start justify-between mb-3">
        <h2 className="text-xl font-semibold text-gray-900 line-clamp-2">
          {post.title}
        </h2>
        {post.featured && (
          <span className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded">
            Featured
          </span>
        )}
      </div>
      
      <p className="text-gray-600 mb-4 line-clamp-3">
        {post.excerpt}
      </p>
      
      <div className="flex items-center justify-between text-sm text-gray-500">
        <time dateTime={post.publishedAt}>
          {new Date(post.publishedAt).toLocaleDateString()}
        </time>
        <span>{post.readTime} min read</span>
      </div>
      
      {post.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {post.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="bg-gray-100 text-gray-700 text-xs px-2 py-1 rounded"
            >
              {tag}
            </span>
          ))}
          {post.tags.length > 3 && (
            <span className="text-gray-500 text-xs">
              +{post.tags.length - 3} more
            </span>
          )}
        </div>
      )}
    </article>
  )
})

// Performance-optimized project card
interface ProjectCardProps {
  project: {
    id: string
    title: string
    description: string
    imageUrl?: string
    technologies: string[]
    githubUrl?: string
    demoUrl?: string
    featured: boolean
  }
}

export const ProjectCard = memo<ProjectCardProps>(({ project }) => {
  const [ref, isVisible] = useIntersectionObserver({
    threshold: 0.1,
    rootMargin: '100px',
  })
  
  return (
    <div ref={ref} className="bg-white rounded-lg shadow-md overflow-hidden">
      {project.imageUrl && isVisible && (
        <OptimizedImage
          src={project.imageUrl}
          alt={project.title}
          className="w-full h-48 object-cover"
          width={400}
          height={200}
        />
      )}
      
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <h3 className="text-lg font-semibold text-gray-900">
            {project.title}
          </h3>
          {project.featured && (
            <span className="bg-green-100 text-green-800 text-xs font-medium px-2.5 py-0.5 rounded">
              Featured
            </span>
          )}
        </div>
        
        <p className="text-gray-600 mb-4 line-clamp-3">
          {project.description}
        </p>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {project.technologies.slice(0, 4).map((tech) => (
            <span
              key={tech}
              className="bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded"
            >
              {tech}
            </span>
          ))}
          {project.technologies.length > 4 && (
            <span className="text-gray-500 text-xs">
              +{project.technologies.length - 4} more
            </span>
          )}
        </div>
        
        <div className="flex gap-3">
          {project.githubUrl && (
            <a
              href={project.githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              GitHub
            </a>
          )}
          {project.demoUrl && (
            <a
              href={project.demoUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 transition-colors"
            >
              Live Demo
            </a>
          )}
        </div>
      </div>
    </div>
  )
})

// Lazy loading wrapper component
interface LazyComponentWrapperProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  minHeight?: number
}

export const LazyComponentWrapper = memo<LazyComponentWrapperProps>(({
  children,
  fallback = <LoadingSkeleton />,
  minHeight = 200
}) => (
  <Suspense fallback={
    <div style={{ minHeight: `${minHeight}px` }} className="flex items-center justify-center">
      {fallback}
    </div>
  }>
    {children}
  </Suspense>
))

// Performance monitoring hook
export const usePerformanceMonitor = () => {
  React.useEffect(() => {
    // Monitor Core Web Vitals
    const observer = new PerformanceObserver((list) => {
      list.getEntries().forEach((entry) => {
        if (entry.entryType === 'largest-contentful-paint') {
          console.log('LCP:', entry.startTime)
        }
        if (entry.entryType === 'first-input') {
          console.log('FID:', (entry as any).processingStart - entry.startTime)
        }
        if (entry.entryType === 'layout-shift') {
          console.log('CLS:', (entry as any).value)
        }
      })
    })
    
    observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] })
    
    return () => observer.disconnect()
  }, [])
}

// Export lazy components
export const LazyBlogEditor = () => (
  <LazyComponentWrapper minHeight={400}>
    <BlogEditor />
  </LazyComponentWrapper>
)

export const LazyProjectGallery = () => (
  <LazyComponentWrapper minHeight={600}>
    <ProjectGallery />
  </LazyComponentWrapper>
)

export const LazyAnalyticsChart = () => (
  <LazyComponentWrapper minHeight={300}>
    <AnalyticsChart />
  </LazyComponentWrapper>
)

export const LazySkillsVisualization = () => (
  <LazyComponentWrapper minHeight={400}>
    <SkillsVisualization />
  </LazyComponentWrapper>
)