---
name: document_writer
description: This skill helps the user to write document for a project when they ask questions like "Please introduce X project", "Please write a document to introduce X project", "What does the project X do", or show interest in gathering information about some project. 
---

# Document Writer

This skill helps the user to write high quality document to introduce a project.

## FIRST STEP: PREVIEW THE PROJECT STRUCTURE

在后文的描述中，$PROJECT_ROOT 将被用来表示用户所感兴趣的项目所在的根目录。在这一步，你首先需要简单查看项目的目录结构，以此来对项目有一个大致的了解:

```bash
ls -la $PROJECT_ROOT
```

## SECOND STEP: LOOK AT THE PROJECT REQUIREMENTS AND DEVELOPMENT HISTORY

在简单了解了项目的目录结构之后，你需要在这个项目中查看下面几个文件来了解项目的大致需求和开发历史:

```bash
# 1. 项目需求文档
cat $PROJECT_ROOT/app_spec.md

# 2. 项目开发过程
cat $PROJECT_ROOT/tasks.json

# 3. 项目增量式开发过程
cat $PROJECT_ROOT/requirements.json
```

## THIRD STEP: LOOK AT THE SOURCE FILES OF THE PROJECT

在了解了项目具体的目录结构、项目需求和开发历史之后，你需要进一步查看项目的源代码结构:

```bash
ls -la $PROJECT_ROOT/src
```

在必要的情况下，你可以使用`ReadFile`工具对源码进行查看。

## FOURTH STEP: WRITE A DOCUMENT TO INTRODUCE THE PROJECT

在这一步，你需要根据你对项目的理解输出一个高质量的文档，并写在文件`DOCUMENT.md`中，文档内容应该包括:
- 这个项目的作用主要是什么
- 如何编译这个项目
- 这个项目的主要实现细节，在实现细节里包含下面的内容:
    - 使用`mermaid`绘制一个项目的类图，展示项目中不同类之间的关系
    - 文字介绍每一个类的主要功能和API文档
    - 使用`mermaid`绘制一个或者多个时序图，展示运行过程
    - 使用`mermaid`绘制一个数据流图，展示各个模块之间的关系

## LANGUAGE PREFERENCE
你必须使用中文进行文档书写
