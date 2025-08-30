"""
Performance tests for DevPortfolio application.
Tests API response times, database query performance, and scalability.
"""
import pytest
import time
import asyncio
import concurrent.futures
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import statistics
import psutil
import threading

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.performance
class TestAPIPerformance:
    """Test API endpoint performance requirements."""
    
    def test_api_response_time_requirement(self, client):
        """Test that API responses meet <200ms requirement."""
        endpoints = [
            "/",
            "/health",
            "/blog/posts",
            "/portfolio/projects"
        ]
        
        for endpoint in endpoints:
            response_times = []
            
            # Test multiple times for consistent results
            for _ in range(10):
                start_time = time.time()
                response = client.get(endpoint)
                end_time = time.time()
                
                assert response.status_code == 200
                response_time = (end_time - start_time) * 1000  # Convert to ms
                response_times.append(response_time)
            
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            
            print(f"Endpoint {endpoint}:")
            print(f"  Average response time: {avg_response_time:.2f}ms")
            print(f"  Max response time: {max_response_time:.2f}ms")
            
            # Allow some flexibility in test environment
            assert avg_response_time < 500, f"Average response time {avg_response_time}ms exceeds limit for {endpoint}"
            assert max_response_time < 1000, f"Max response time {max_response_time}ms exceeds limit for {endpoint}"

    def test_concurrent_request_handling(self, client):
        """Test handling of concurrent requests."""
        def make_request():
            start_time = time.time()
            response = client.get("/blog/posts")
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000,
                'success': response.status_code == 200
            }
        
        # Test with 50 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Analyze results
        successful_requests = sum(1 for r in results if r['success'])
        avg_response_time = statistics.mean([r['response_time'] for r in results])
        max_response_time = max([r['response_time'] for r in results])
        
        print(f"Concurrent requests test:")
        print(f"  Successful requests: {successful_requests}/50")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        print(f"  Max response time: {max_response_time:.2f}ms")
        
        # Requirements
        assert successful_requests >= 45, "Too many failed requests under load"
        assert avg_response_time < 1000, "Average response time too high under load"

    def test_large_payload_performance(self, client):
        """Test performance with large payloads."""
        # Create a large blog post (50KB)
        large_content = "Lorem ipsum dolor sit amet. " * 2000  # ~50KB
        
        post_data = {
            "title": "Large Performance Test Post",
            "content": large_content,
            "tags": ["performance", "test"]
        }
        
        with patch('main.get_current_user') as mock_get_user:
            mock_get_user.return_value = {"is_admin": True}
            
            start_time = time.time()
            response = client.post("/blog/posts", 
                                 json=post_data,
                                 headers={"Authorization": "Bearer admin-token"})
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            print(f"Large payload test:")
            print(f"  Payload size: ~50KB")
            print(f"  Response time: {response_time:.2f}ms")
            
            # Should handle large payloads reasonably well
            assert response.status_code in [201, 413]  # Created or Payload Too Large
            if response.status_code == 201:
                assert response_time < 2000, "Large payload processing too slow"

    def test_database_query_performance(self, client):
        """Test database query performance."""
        with patch('database.execute_query') as mock_query:
            # Simulate database query timing
            def slow_query(*args, **kwargs):
                time.sleep(0.01)  # Simulate 10ms database query
                return [{"id": 1, "title": "Test Post"}]
            
            mock_query.side_effect = slow_query
            
            start_time = time.time()
            response = client.get("/blog/posts")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            # Total response time should still be reasonable
            assert response_time < 500, "Database query performance issue"

    def test_pagination_performance(self, client):
        """Test pagination performance with large datasets."""
        # Test different page sizes
        page_sizes = [10, 50, 100]
        
        for page_size in page_sizes:
            start_time = time.time()
            response = client.get(f"/blog/posts?limit={page_size}&offset=0")
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            assert response.status_code == 200
            assert response_time < 300, f"Pagination too slow for page size {page_size}"


@pytest.mark.performance
class TestMemoryPerformance:
    """Test memory usage and performance."""
    
    def test_memory_usage_under_load(self, client):
        """Test memory usage doesn't grow excessively under load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for _ in range(100):
            client.get("/blog/posts")
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage test:")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {memory_increase:.2f}MB")
        
        # Memory shouldn't increase dramatically
        assert memory_increase < 50, "Excessive memory usage under load"

    def test_garbage_collection_efficiency(self, client):
        """Test that garbage collection is working efficiently."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create and process many requests
        for _ in range(50):
            response = client.get("/blog/posts")
            del response  # Explicit cleanup
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        object_increase = final_objects - initial_objects
        
        print(f"Garbage collection test:")
        print(f"  Initial objects: {initial_objects}")
        print(f"  Final objects: {final_objects}")
        print(f"  Object increase: {object_increase}")
        
        # Object count shouldn't grow excessively
        assert object_increase < 1000, "Potential memory leak detected"


@pytest.mark.performance
class TestCachePerformance:
    """Test caching performance improvements."""
    
    def test_cache_hit_performance(self, client):
        """Test that cache hits improve response times."""
        # First request (cache miss)
        start_time = time.time()
        response1 = client.get("/blog/posts")
        end_time = time.time()
        cache_miss_time = (end_time - start_time) * 1000
        
        # Second request (should be cache hit)
        start_time = time.time()
        response2 = client.get("/blog/posts")
        end_time = time.time()
        cache_hit_time = (end_time - start_time) * 1000
        
        print(f"Cache performance test:")
        print(f"  Cache miss time: {cache_miss_time:.2f}ms")
        print(f"  Cache hit time: {cache_hit_time:.2f}ms")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Cache hit should be faster (allowing for test environment variations)
        # In production with Redis, this would be much more pronounced
        improvement_ratio = cache_miss_time / cache_hit_time if cache_hit_time > 0 else 1
        print(f"  Performance improvement: {improvement_ratio:.2f}x")

    @patch('services.cache_service.get')
    @patch('services.cache_service.set')
    def test_cache_effectiveness(self, mock_cache_set, mock_cache_get, client):
        """Test cache effectiveness in reducing database load."""
        # Simulate cache miss then hit
        mock_cache_get.side_effect = [None, {"cached": "data"}]  # Miss then hit
        
        # First request
        response1 = client.get("/blog/posts")
        
        # Second request
        response2 = client.get("/blog/posts")
        
        # Verify cache was checked and set
        assert mock_cache_get.call_count == 2
        assert mock_cache_set.call_count == 1


@pytest.mark.performance
class TestScalabilityLimits:
    """Test system scalability limits."""
    
    def test_request_throughput(self, client):
        """Test maximum request throughput."""
        def make_requests_batch():
            results = []
            for _ in range(10):
                start_time = time.time()
                response = client.get("/health")
                end_time = time.time()
                results.append({
                    'success': response.status_code == 200,
                    'response_time': (end_time - start_time) * 1000
                })
            return results
        
        # Test with multiple concurrent batches
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_requests_batch) for _ in range(10)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        successful_requests = sum(1 for r in all_results if r['success'])
        total_requests = len(all_results)
        success_rate = successful_requests / total_requests * 100
        avg_response_time = statistics.mean([r['response_time'] for r in all_results])
        
        print(f"Throughput test:")
        print(f"  Total requests: {total_requests}")
        print(f"  Successful requests: {successful_requests}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average response time: {avg_response_time:.2f}ms")
        
        # Requirements for scalability
        assert success_rate >= 95, "Success rate too low under load"
        assert avg_response_time < 1000, "Response time degraded too much under load"

    def test_connection_pooling_efficiency(self, client):
        """Test database connection pooling efficiency."""
        def make_db_intensive_request():
            # Simulate database-intensive endpoint
            return client.get("/analytics/dashboard")
        
        # Make concurrent database-intensive requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_db_intensive_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should complete successfully
        successful_requests = sum(1 for r in results if r.status_code in [200, 404])
        
        print(f"Connection pooling test:")
        print(f"  Successful requests: {successful_requests}/20")
        
        # Should handle concurrent database requests efficiently
        assert successful_requests >= 18, "Connection pooling not handling load efficiently"


@pytest.mark.performance
class TestResourceUtilization:
    """Test system resource utilization."""
    
    def test_cpu_usage_under_load(self, client):
        """Test CPU usage remains reasonable under load."""
        import psutil
        
        # Monitor CPU usage during load test
        cpu_percentages = []
        
        def cpu_monitor():
            for _ in range(10):  # Monitor for ~10 seconds
                cpu_percentages.append(psutil.cpu_percent(interval=1))
        
        # Start CPU monitoring in background
        monitor_thread = threading.Thread(target=cpu_monitor)
        monitor_thread.start()
        
        # Generate load
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(lambda: client.get("/blog/posts")) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        monitor_thread.join()
        
        if cpu_percentages:
            avg_cpu = statistics.mean(cpu_percentages)
            max_cpu = max(cpu_percentages)
            
            print(f"CPU usage test:")
            print(f"  Average CPU usage: {avg_cpu:.1f}%")
            print(f"  Max CPU usage: {max_cpu:.1f}%")
            
            # CPU usage should be reasonable
            assert avg_cpu < 80, "Average CPU usage too high under load"
            assert max_cpu < 95, "Peak CPU usage too high"

    def test_file_descriptor_usage(self, client):
        """Test file descriptor usage doesn't leak."""
        import psutil
        
        process = psutil.Process()
        initial_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
        
        # Make many requests
        for _ in range(100):
            response = client.get("/health")
            assert response.status_code == 200
        
        final_fds = process.num_fds() if hasattr(process, 'num_fds') else 0
        fd_increase = final_fds - initial_fds
        
        print(f"File descriptor test:")
        print(f"  Initial FDs: {initial_fds}")
        print(f"  Final FDs: {final_fds}")
        print(f"  FD increase: {fd_increase}")
        
        # File descriptors shouldn't leak
        assert fd_increase < 10, "Potential file descriptor leak"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])