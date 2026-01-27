# 如何创建 module-info.java 让程序在 IntelliJ IDEA 中直接运行

## 前提条件

1. **Java 9+**：module-info.java 需要 Java 9 或更高版本
2. **项目结构**：确保项目有标准的 Maven/Gradle 目录结构

## 步骤

### 1. 确定模块名称

模块名称通常与项目的根包名相同，例如：
- 如果包名是 `com.example.myapp`，模块名可以是 `com.example.myapp`
- 或者使用项目名称，如 `myapp`

### 2. 创建 module-info.java 文件

在 `src/main/java` 目录下创建 `module-info.java` 文件（与包目录同级）

**基本模板：**

```java
module your.module.name {
    // 导出当前模块的包（供其他模块使用）
    exports com.yourcompany.package1;
    exports com.yourcompany.package2;
    
    // 声明依赖的外部模块
    requires java.base;                    // 默认包含，可省略
    requires java.desktop;                  // Swing/AWT
    requires java.sql;                      // JDBC
    requires java.net.http;                 // HTTP Client
    
    // 如果使用第三方库，需要添加
    requires org.slf4j;                     // 示例：SLF4J
    requires com.fasterxml.jackson.core;    // 示例：Jackson
    
    // 如果使用反射访问，需要打开包
    opens com.yourcompany.package1;
    
    // 如果使用服务提供者模式
    uses com.yourcompany.ServiceInterface;
    provides com.yourcompany.ServiceInterface 
        with com.yourcompany.ServiceImpl;
}
```

### 3. 常见依赖模块映射

| 功能 | 模块名 |
|------|--------|
| 基础功能 | `java.base` (默认) |
| Swing/AWT GUI | `java.desktop` |
| 数据库 | `java.sql` |
| HTTP 客户端 | `java.net.http` |
| XML 处理 | `java.xml` |
| 日志 (java.util.logging) | `java.logging` |
| JSON (Jackson) | `com.fasterxml.jackson.core`, `com.fasterxml.jackson.databind` |
| JSON (Gson) | `com.google.gson` |
| Spring Framework | `spring.core`, `spring.context` 等 |
| JUnit 5 | `org.junit.jupiter.api` |

### 4. 在 IntelliJ IDEA 中配置

#### 方法 A：自动检测（推荐）

1. 创建 `module-info.java` 后，IntelliJ IDEA 会自动检测
2. 如果出现错误，点击错误提示，IDEA 会建议添加缺失的 `requires` 语句

#### 方法 B：手动配置项目结构

1. **File** → **Project Structure** (Ctrl+Alt+Shift+S)
2. 选择 **Modules**
3. 确保 **Language level** 设置为 **9** 或更高
4. 在 **Sources** 标签页，确认 `src/main/java` 被标记为 **Sources**
5. 在 **Dependencies** 标签页，添加所需的库

### 5. 示例：完整的 module-info.java

假设你的项目结构如下：
```
src/main/java/
  ├── module-info.java
  └── com/
      └── example/
          └── myapp/
              ├── Main.java
              ├── service/
              └── util/
```

**module-info.java：**

```java
module com.example.myapp {
    // 导出主包
    exports com.example.myapp;
    exports com.example.myapp.service;
    
    // 基础依赖（通常自动包含）
    // requires java.base;  // 可省略
    
    // 如果需要 GUI
    requires java.desktop;
    
    // 如果需要数据库
    requires java.sql;
    
    // 如果需要 HTTP 客户端
    requires java.net.http;
    
    // 第三方库示例（根据实际使用的库添加）
    // requires org.slf4j;
    // requires com.fasterxml.jackson.databind;
    
    // 如果使用反射，需要打开包
    opens com.example.myapp to java.base;
}
```

### 6. 处理常见问题

#### 问题 1：找不到模块

**错误信息：** `module not found: xxx`

**解决方案：**
- 检查模块名是否正确
- 确认依赖库是否支持模块系统
- 对于不支持模块系统的 JAR，可能需要使用 `--add-modules` 或转换为自动模块

#### 问题 2：包未导出

**错误信息：** `package xxx is not visible`

**解决方案：**
- 在 `module-info.java` 中添加 `exports xxx;`
- 或者如果只需要反射访问，使用 `opens xxx;`

#### 问题 3：第三方库不支持模块系统

**解决方案：**
- 如果 JAR 文件在类路径上（classpath），它们会自动成为"未命名模块"
- 或者将 JAR 放在模块路径上，它们会成为"自动模块"（automatic module）
- 自动模块的名称通常是 JAR 文件名（去掉版本号）

### 7. 运行配置

在 IntelliJ IDEA 中：

1. **Run** → **Edit Configurations**
2. 选择你的运行配置
3. 在 **VM options** 中，如果需要可以添加：
   ```
   --module-path <path-to-modules>
   --add-modules <module-name>
   ```
4. 在 **Program arguments** 中：
   ```
   --module your.module.name/com.yourcompany.Main
   ```

### 8. 快速检查清单

- [ ] `module-info.java` 位于 `src/main/java/` 目录下
- [ ] 模块名与项目包名一致（或合理）
- [ ] 所有使用的包都已导出（exports）
- [ ] 所有外部依赖都已声明（requires）
- [ ] Java 版本设置为 9 或更高
- [ ] IntelliJ IDEA 已识别模块结构

### 9. 从 Maven 项目迁移

如果你的项目使用 Maven：

1. **保持 pom.xml**：module-info.java 与 Maven 兼容
2. **检查依赖**：确保 Maven 依赖支持模块系统
3. **运行方式**：
   - **Maven run**：`mvn exec:java` 或 `mvn spring-boot:run`
   - **IntelliJ 直接运行**：创建运行配置，指向主类

### 10. 示例：Spring Boot 项目

```java
module com.example.springapp {
    requires spring.boot;
    requires spring.boot.autoconfigure;
    requires spring.context;
    requires spring.web;
    
    requires java.desktop;
    
    exports com.example.springapp;
    opens com.example.springapp to spring.core, spring.beans;
}
```

## 注意事项

1. **模块名命名**：使用反向域名格式，如 `com.company.project`
2. **不要循环依赖**：模块之间不能相互依赖
3. **反射访问**：如果使用反射，必须使用 `opens` 而不是 `exports`
4. **测试模块**：测试代码通常放在单独的测试模块或使用 `--add-opens` 参数

## 参考资源

- [Java Platform Module System (JPMS) 官方文档](https://openjdk.java.net/projects/jigsaw/)
- [IntelliJ IDEA 模块系统支持](https://www.jetbrains.com/help/idea/working-with-modules.html)

