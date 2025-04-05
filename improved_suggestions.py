def enhanced_update_suggestions_list_with_data(self):
    """Update the suggestions list with actual data using improved organization by sentiment"""
    if not self.simulation_results:
        self.suggestions_text.delete("1.0", "end")
        self.suggestions_text.insert("1.0", "# No Data\n\nNo simulation results available to generate suggestions.")
        return
            
    # Extract all suggestions with their source result for context
    suggestion_items = []
    
    for result in self.simulation_results:
        sentiment = result.get("sentiment", "neutral")
        statement = result.get("statement", "")
        department = result.get("department", "Unknown")
        role = result.get("role", "Unknown")
        
        if "suggestions" in result and result["suggestions"]:
            for suggestion in result["suggestions"]:
                suggestion_text = suggestion.strip()
                if suggestion_text:  # Only add non-empty suggestions
                    suggestion_items.append({
                        "text": suggestion_text,
                        "sentiment": sentiment,
                        "statement": statement,
                        "department": department,
                        "role": role
                    })
    
    if not suggestion_items:
        self.suggestions_text.delete("1.0", "end")
        self.suggestions_text.insert("1.0", "# No Suggestions\n\nNo specific suggestions were provided in the feedback.")
        return
    
    # Group suggestions by sentiment
    favorable_suggestions = [item for item in suggestion_items if item["sentiment"] == "favorable"]
    neutral_suggestions = [item for item in suggestion_items if item["sentiment"] == "neutral"]
    unfavorable_suggestions = [item for item in suggestion_items if item["sentiment"] == "unfavorable"]
    
    # Reset the sampler for fresh sampling
    self.verbal_sampling_manager.reset()
    
    # Try to use embeddings to cluster similar suggestions
    suggestion_clusters = self.cluster_similar_suggestions(suggestion_items)
    
    # Calculate percentages
    total_results = len(self.simulation_results)
    
    # Generate suggestions text
    suggestions_text = "# Improvement Suggestions\n\n"
    suggestions_text += f"Based on feedback from {total_results} associates, here are grouped suggestions to improve reception:\n\n"
    
    # Add section for suggestion clusters
    if suggestion_clusters:
        suggestions_text += "## Clustered Suggestions\n\n"
        
        for i, cluster in enumerate(suggestion_clusters, 1):
            if len(cluster) > 0:
                # Calculate what percentage of results included suggestions in this cluster
                cluster_percentage = round((len(cluster) / total_results) * 100)
                
                # Get the most representative suggestion as the label
                representative = cluster[0]["text"]
                for item in cluster:
                    if len(item["text"]) > len(representative) and len(item["text"]) < 100:
                        representative = item["text"]
                
                suggestions_text += f"### {i}. {representative}\n"
                suggestions_text += f"*({cluster_percentage}% of respondents suggested similar ideas)*\n\n"
                
                # Show sentiment breakdown for this cluster
                favorable_count = sum(1 for item in cluster if item["sentiment"] == "favorable")
                neutral_count = sum(1 for item in cluster if item["sentiment"] == "neutral")
                unfavorable_count = sum(1 for item in cluster if item["sentiment"] == "unfavorable")
                
                if favorable_count > 0:
                    fav_pct = round((favorable_count / len(cluster)) * 100)
                    suggestions_text += f"- 🟢 {fav_pct}% of these came from favorable feedback\n"
                if neutral_count > 0:
                    neu_pct = round((neutral_count / len(cluster)) * 100)
                    suggestions_text += f"- 🟡 {neu_pct}% of these came from neutral feedback\n"
                if unfavorable_count > 0:
                    unfav_pct = round((unfavorable_count / len(cluster)) * 100)
                    suggestions_text += f"- 🔴 {unfav_pct}% of these came from unfavorable feedback\n"
                
                suggestions_text += "\n"
                
                # Show sample suggestions with context quotes
                sample_size = min(3, len(cluster))
                diverse_samples = self.verbal_sampling_manager.select_diverse_statements(
                    [item["text"] for item in cluster],
                    n=sample_size
                )
                
                suggestions_text += "**Sample variations:**\n"
                for sample_text in diverse_samples:
                    # Find the matching item
                    matching_items = [item for item in cluster if item["text"] == sample_text]
                    if matching_items:
                        item = matching_items[0]
                        dept_role = f"{item['department']} {item['role']}"
                        suggestions_text += f"- \"{sample_text}\" *({dept_role})*\n"
                
                suggestions_text += "\n"
                
                # Show supporting quotes
                sample_statements = []
                for sentiment_group in ["favorable", "neutral", "unfavorable"]:
                    items = [item for item in cluster if item["sentiment"] == sentiment_group and item["statement"]]
                    if items:
                        # Get one diverse statement from this sentiment group
                        statements = [item["statement"] for item in items]
                        if statements:
                            diverse_statement = self.verbal_sampling_manager.select_diverse_statements(
                                statements,
                                n=1
                            )
                            if diverse_statement:
                                # Find the matching item
                                matching_items = [item for item in items if item["statement"] == diverse_statement[0]]
                                if matching_items:
                                    item = matching_items[0]
                                    sample_statements.append({
                                        "text": item["statement"],
                                        "sentiment": item["sentiment"],
                                        "department": item["department"],
                                        "role": item["role"]
                                    })
                
                if sample_statements:
                    suggestions_text += "**Supporting feedback:**\n"
                    for stmt in sample_statements:
                        sentiment_emoji = "🟢" if stmt["sentiment"] == "favorable" else "🟡" if stmt["sentiment"] == "neutral" else "🔴"
                        dept_role = f"{stmt['department']} {stmt['role']}"
                        suggestions_text += f"{sentiment_emoji} \"{stmt['text']}\" *({dept_role})*\n\n"
    
    # Add sections by sentiment type
    sentiment_sections = []
    
    # Only add sections for sentiments that have suggestions
    if favorable_suggestions:
        sentiment_sections.append({
            "title": "From Favorable Feedback",
            "emoji": "🟢",
            "items": favorable_suggestions,
            "description": "These suggestions come from associates who generally support the proposal:"
        })
    
    if neutral_suggestions:
        sentiment_sections.append({
            "title": "From Neutral Feedback",
            "emoji": "🟡",
            "items": neutral_suggestions,
            "description": "These suggestions come from associates with mixed or neutral feelings about the proposal:"
        })
    
    if unfavorable_suggestions:
        sentiment_sections.append({
            "title": "From Critical Feedback",
            "emoji": "🔴",
            "items": unfavorable_suggestions,
            "description": "These suggestions come from associates who expressed concerns about the proposal:"
        })
    
    if sentiment_sections:
        suggestions_text += "## Suggestions by Sentiment\n\n"
        
        for section in sentiment_sections:
            suggestions_text += f"### {section['emoji']} {section['title']}\n"
            suggestions_text += f"{section['description']}\n\n"
            
            # Group suggestions by department for context
            dept_suggestions = {}
            for item in section["items"]:
                dept = item["department"]
                if dept not in dept_suggestions:
                    dept_suggestions[dept] = []
                dept_suggestions[dept].append(item)
            
            # Show sample suggestions from each department
            for dept, items in dept_suggestions.items():
                if len(dept_suggestions) > 1:  # Only show department headers if there's more than one
                    suggestions_text += f"**{dept} Department:**\n"
                
                # Select diverse suggestions from this department
                sample_size = min(3, len(items))
                diverse_texts = self.verbal_sampling_manager.select_diverse_statements(
                    [item["text"] for item in items],
                    n=sample_size
                )
                
                for sample_text in diverse_texts:
                    # Find the matching item
                    matching_items = [item for item in items if item["text"] == sample_text]
                    if matching_items:
                        item = matching_items[0]
                        suggestions_text += f"- \"{item['text']}\" *({item['role']})*\n"
                        
                        # Add the statement that led to this suggestion
                        if item["statement"]:
                            suggestions_text += f"  - *\"{item['statement']}\"*\n"
                
                suggestions_text += "\n"
    
    # Add executive summary of key recommendations
    suggestions_text += "## Executive Summary\n\n"
    
    # Highlight cross-sentiment suggestions if any exist
    cross_sentiment_clusters = [c for c in suggestion_clusters if len(set(item["sentiment"] for item in c)) > 1]
    if cross_sentiment_clusters:
        # Sort by size (largest first)
        cross_sentiment_clusters.sort(key=len, reverse=True)
        largest_cross_cluster = cross_sentiment_clusters[0]
        
        # Get the most representative suggestion
        representative = largest_cross_cluster[0]["text"]
        for item in largest_cross_cluster:
            if len(item["text"]) > len(representative) and len(item["text"]) < 100:
                representative = item["text"]
        
        # Calculate percentage
        cross_cluster_percentage = round((len(largest_cross_cluster) / total_results) * 100)
        
        suggestions_text += f"The most broadly supported recommendation (from associates with differing views) is:\n\n"
        suggestions_text += f"**{representative}** *({cross_cluster_percentage}% of respondents)*\n\n"
    else:
        # Just use the largest cluster
        largest_cluster = max(suggestion_clusters, key=len) if suggestion_clusters else []
        if largest_cluster:
            # Get the most representative suggestion
            representative = largest_cluster[0]["text"]
            for item in largest_cluster:
                if len(item["text"]) > len(representative) and len(item["text"]) < 100:
                    representative = item["text"]
            
            # Calculate percentage
            cluster_percentage = round((len(largest_cluster) / total_results) * 100)
            
            suggestions_text += f"The most common recommendation is:\n\n"
            suggestions_text += f"**{representative}** *({cluster_percentage}% of respondents)*\n\n"
    
    self.suggestions_text.delete("1.0", "end")
    self.suggestions_text.insert("1.0", suggestions_text)

def cluster_similar_suggestions(self, suggestion_items):
    """
    Group similar suggestions into clusters based on semantic similarity
    
    Args:
        suggestion_items: List of dictionaries containing suggestion text and metadata
        
    Returns:
        List of clusters, where each cluster is a list of suggestion items
    """
    if not suggestion_items:
        return []
    
    # Extract unique suggestion texts
    unique_texts = []
    text_to_items = {}
    
    for item in suggestion_items:
        text = item["text"]
        if text not in text_to_items:
            unique_texts.append(text)
            text_to_items[text] = []
        text_to_items[text].append(item)
    
    # If we only have a few suggestions, don't bother clustering
    if len(unique_texts) <= 5:
        return [text_to_items[text] for text in unique_texts]
    
    # Try to use embedding helper if available
    if hasattr(self, "embedding_helper") and self.embedding_helper and self.embedding_helper.available:
        try:
            # Get embeddings for all texts
            text_embeddings = {}
            for text in unique_texts:
                embedding = self.embedding_helper.get_embedding(text)
                if embedding is not None:
                    text_embeddings[text] = embedding
            
            # If we got embeddings, use them for clustering
            if text_embeddings:
                from sklearn.cluster import AgglomerativeClustering
                import numpy as np
                
                # Prepare the embedding matrix
                texts_with_embeddings = list(text_embeddings.keys())
                embedding_matrix = np.array([text_embeddings[text] for text in texts_with_embeddings])
                
                # Determine optimal number of clusters (between 3 and 7)
                from sklearn.metrics import silhouette_score
                
                best_score = -1
                best_n_clusters = 3
                
                for n_clusters in range(3, min(8, len(texts_with_embeddings))):
                    clustering = AgglomerativeClustering(n_clusters=n_clusters)
                    cluster_labels = clustering.fit_predict(embedding_matrix)
                    
                    if len(set(cluster_labels)) > 1:  # Ensure we have more than one cluster
                        score = silhouette_score(embedding_matrix, cluster_labels)
                        if score > best_score:
                            best_score = score
                            best_n_clusters = n_clusters
                
                # Cluster the suggestions
                clustering = AgglomerativeClustering(n_clusters=best_n_clusters)
                cluster_labels = clustering.fit_predict(embedding_matrix)
                
                # Group texts by cluster
                clusters = [[] for _ in range(best_n_clusters)]
                for i, text in enumerate(texts_with_embeddings):
                    label = cluster_labels[i]
                    clusters[label].extend(text_to_items[text])
                
                # Filter out empty clusters
                clusters = [c for c in clusters if c]
                
                return clusters
        except Exception as e:
            print(f"Error in embedding-based clustering: {str(e)}")
            # Fall through to simpler methods
    
    # Fallback: Use simple text similarity for clustering
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import AgglomerativeClustering
        
        # Create TF-IDF vectors
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(unique_texts)
        
        # Cluster the suggestions (aim for 3-5 clusters depending on number of suggestions)
        n_clusters = min(max(3, len(unique_texts) // 3), 5)
        clustering = AgglomerativeClustering(
            n_clusters=n_clusters,
            affinity='euclidean',
            linkage='ward'
        )
        
        from scipy.sparse import csr_matrix
        if isinstance(tfidf_matrix, csr_matrix):
            # Convert sparse matrix to dense if needed
            tfidf_matrix = tfidf_matrix.toarray()
            
        cluster_labels = clustering.fit_predict(tfidf_matrix)
        
        # Group texts by cluster
        clusters = [[] for _ in range(n_clusters)]
        for i, text in enumerate(unique_texts):
            label = cluster_labels[i]
            clusters[label].extend(text_to_items[text])
        
        # Filter out empty clusters
        clusters = [c for c in clusters if c]
        
        return clusters
        
    except Exception as e:
        print(f"Error in TF-IDF clustering: {str(e)}")
        
        # Super simple fallback: just group by first word
        clusters = {}
        for text in unique_texts:
            first_word = text.split()[0].lower() if text.split() else "misc"
            if first_word not in clusters:
                clusters[first_word] = []
            clusters[first_word].extend(text_to_items[text])
        
        # Convert to list of clusters
        cluster_list = list(clusters.values())
        
        # Merge very small clusters if we have too many
        if len(cluster_list) > 7:
            # Sort by size
            cluster_list.sort(key=len, reverse=True)
            
            # Keep the top 5, merge the rest
            merged_cluster = []
            for i in range(5, len(cluster_list)):
                merged_cluster.extend(cluster_list[i])
            
            if merged_cluster:
                result_clusters = cluster_list[:5]
                result_clusters.append(merged_cluster)
                return result_clusters
        
        return cluster_list