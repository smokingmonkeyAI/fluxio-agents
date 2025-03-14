# Fluxio Agents

A Python server that serves as the foundation for a developer agent system. This system processes code repositories and requirements documents, storing them in vector and graph databases to enable intelligent code understanding and manipulation.

## Architecture

```mermaid
flowchart TB
    subgraph "Developer Agent System"
        LLM[LLM Service] 
        Agent[Developer Agent]
        Parser[Code Parser/Chunker]
        EmbeddingEngine[Embedding Engine]
    end
    
    subgraph "Vector Storage"
        Qdrant[(Qdrant Vector DB)]
        subgraph "Vector Collections"
            CodeChunks[Code Chunks]
            DocChunks[Documentation Chunks]
            RequirementChunks[Requirement Chunks]
        end
    end
    
    subgraph "Relationship Storage"
        Neo4j[(Neo4j Graph DB)]
        subgraph "Graph Nodes"
            Files[File Nodes]
            Functions[Function Nodes]
            Classes[Class Nodes]
            Requirements[Requirement Nodes]
            Features[Feature Nodes]
        end
    end
    
    CodeRepo[Code Repository] --> Parser
    RequirementsDoc[Requirements Documents] --> Parser
    
    Parser --> EmbeddingEngine
    EmbeddingEngine --> Qdrant
    
    Parser --> Neo4j
    
    Agent <--> LLM
    Agent <--> Qdrant
    Agent <--> Neo4j
    
    Qdrant -- "ID References" --> Neo4j
    Neo4j -- "Vector IDs" --> Qdrant
```

## Core Components

1. **Developer Agent**: Interfaces with the LLM service and databases to perform development tasks
2. **Code Parser/Chunker**: Processes code repositories and requirements documents
3. **Embedding Engine**: Converts code and documentation into vector embeddings
4. **Vector Storage (Qdrant)**: Stores embeddings for semantic search
5. **Relationship Storage (Neo4j)**: Maintains the relationships between code elements

## Getting Started

[Installation and usage instructions will be added]