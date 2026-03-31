# Crawler service

## Architecture

The crawler service is designed to be modular and extensible, allowing for easy integration of new crawlers for different e-commerce platforms. The architecture consists of the following components:

1. **Base Crawler Class**: An abstract class that defines the common interface and functionality for all crawlers. This class can be extended to create specific crawlers for different platforms.
2. **Specific Crawler Implementations**: Concrete implementations of the base crawler class for specific e-commerce platforms (e.g., Amazon, eBay, etc.). Each implementation will handle the unique structure and requirements of its respective platform.
3. **Crawler Manager**: A component responsible for managing the lifecycle of crawlers, including instantiation, execution, and scheduling.
4. **Data Storage**: A peer component to the base crawler that defines schema and constraints, and exposes public functions for persistence, file handling, and optional ETL helpers used by specific crawlers when needed.
5. **Error Handling and Logging**: A system for handling errors and logging the crawling process for debugging and monitoring purposes.

### Architecture Diagram

```
                   +---------------------+
                   |   Crawler Manager   |
                   |  schedule/run jobs  |
                   +----------+----------+
                              |
                              v
                   +---------------------+         +---------------------+
                   |  Base Crawler Class |<------->|     Data Storage    |
                   |  fetch/parse/emit   |         | schema/constraints  |
                   +----------+----------+         | persist/files/ETL   |
                              |                   +----------+----------+
          +-------------------+-------------------+          |
          |                                       |          |
          v                                       v          v
+-----------------------+              +-----------------------+
| Specific Crawler A    |              | Specific Crawler B    |
| site adapters/parsers |              | site adapters/parsers |
+-----------+-----------+              +-----------+-----------+
            |                                       |
            +-------------------+-------------------+
                                |
                                v
                   +---------------------+
                   |  Normalized Output  |
                   |   to Data Storage   |
                   +---------------------+

   Error Handling + Logging (cross-cutting across all components)
```
