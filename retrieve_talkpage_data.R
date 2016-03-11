library(wmf)
library(data.table)
library(magrittr)
library(WikipediR)
library(stringi)
library(urltools)
options(scipen = 500)
dir.create("./data/", showWarnings = FALSE)

# Retrieve logs for a sub-sample of en.wiki talk/discussion pages.
main <- function(){
  
  # Grab the 50 most-edited article talkpages
  article_talk_edit <- wmf::mysql_read("SELECT * FROM (
                                        SELECT page_title AS title, COUNT(*) AS events FROM revision
                                        INNER JOIN page ON rev_page = page_id
                                        WHERE rev_timestamp >= '20160203000000'
                                        AND page_namespace = 1
                                        AND page_title NOT RLIKE('/')
                                        GROUP BY rev_page ORDER BY COUNT(*) DESC) AS inquery
                                        LIMIT 30",
                                        "enwiki")
  article_talk_edit$url <- paste0("https://en.wikipedia.org/wiki/Talk:", article_talk_edit$title)
  article_talk_edit$title <- paste0("Talk:",article_talk_edit$title)
  article_talk_edit$type <- "Article talk"
  article_talk_edit$class <- "Most-edited"
  
  # Random article talkpages
  article_talk_random <- wmf::mysql_read("SELECT * FROM (
                                          SELECT page_title AS title, NULL AS events FROM page
                                          WHERE page_namespace = 1
                                          AND page_is_redirect = 0
                                          AND page_title NOT RLIKE('/')
                                          ORDER BY rand()
                                          ) a1 LIMIT 30;",
                                          "enwiki")
  article_talk_random$url <- paste0("https://en.wikipedia.org/wiki/Talk:", article_talk_random$title)
  article_talk_random$title <- paste0("Talk:",article_talk_random$title)
  article_talk_random$type <- "Article talk"
  article_talk_random$class <- "Random"
  
  # 50 most watchlisted
  user_talk_watchlist <- wmf::mysql_read("SELECT wl_title AS title, COUNT(*) AS events
                                          FROM watchlist INNER JOIN (
                                          SELECT DISTINCT(rc_user) AS users
                                          FROM recentchanges alias1 WHERE rc_bot = 0 AND rc_type = 0) alias2
                                          ON alias2.users = wl_user
                                          INNER JOIN (SELECT page_title FROM page WHERE page_namespace = 3) alias3
                                          ON wl_title = alias3.page_title
                                          WHERE wl_namespace = 3
                                          AND wl_title NOT RLIKE('/')
                                          GROUP BY wl_title
                                          ORDER BY events DESC
                                          LIMIT 30", "enwiki")
  user_talk_watchlist$url <- paste0("https://en.wikipedia.org/wiki/User_talk:", user_talk_watchlist$title)
  user_talk_watchlist$title <- paste0("User_talk:", user_talk_watchlist$title)
  user_talk_watchlist$type <- "User talk"
  user_talk_watchlist$class <- "Most-watched"
  
  # Random talkpages
  user_talk_random <- wmf::mysql_read("SELECT * FROM (
                                       SELECT page_title AS title, NULL AS events FROM page
                                       WHERE page_namespace = 3
                                       AND page_is_redirect = 0
                                       AND page_title NOT RLIKE('/')
                                       ORDER BY rand()
                                       ) a1 LIMIT 30;",
                                      "enwiki")
  
  user_talk_random$url <- paste0("https://en.wikipedia.org/wiki/User_talk:", user_talk_random$title)
  user_talk_random$title <- paste0("User_talk:", user_talk_random$title)
  user_talk_random$type <- "User talk"
  user_talk_random$class <- "Random"
  

  # Bind
  data <- rbind(user_talk_random, user_talk_watchlist, article_talk_random, article_talk_edit)

  # Get info from the API
  revision_ids <- unlist(lapply(data$title, function(page_title){
    cat(".")
    return(WikipediR::page_content("en", "wikipedia", properties = "ids", page_name = url_encode(page_title))$parse$revid)
  }), use.names = FALSE)
  data$url <- paste0(data$url, "?oldid=", revision_ids)
  
  # Check out pageviews
  article_talk_views <- wmf::query_hive("USE wmf; SELECT SUM(view_count) AS events, page_id AS id FROM pageview_hourly
                                        WHERE year = 2016 AND month = 03 AND day BETWEEN 01 AND 07 AND page_title LIKE('Talk:%')
                                        AND page_title NOT RLIKE('/') AND page_id IS NOT NULL
                                        GROUP BY page_id
                                        ORDER BY events DESC LIMIT 100;")
  
  user_talk_views <- wmf::query_hive("USE wmf; SELECT SUM(view_count) AS events, page_id AS id FROM pageview_hourly
                                        WHERE year = 2016 AND month = 03 AND day BETWEEN 01 AND 07 AND page_title LIKE('User_talk:%')
                                        AND page_title NOT RLIKE('/') AND page_id IS NOT NULL
                                        GROUP BY page_id
                                        ORDER BY events DESC LIMIT 100;")
  
  clean <- function(data, type, class){
    view_content <- do.call("rbind", lapply(data$id, function(page_id){
      cat(".")
      content <- try({
        content <- page_content("en", "wikipedia", page_id = page_id)
      }, silent = TRUE)
      if("try-error" %in% class(content)){
        return(data.frame(title = NA, revision = NA))
      }
      return(data.frame(title = content$parse$title, revision = content$parse$revid, stringsAsFactors = FALSE))
    }))
    data <- cbind(data, view_content)
    data <- data[!is.na(data$revision),]
    data <- data[grepl(x = data$title, pattern = "Talk\\:", ignore.case = TRUE),]
    if(type == "User talk"){
      data <- data[grepl(x = data$title, pattern = "User talk:", fixed = TRUE),]
    }
    data$type <- type
    data$class <- class
    return(data[1:30,])
  }
  pageview_data <- rbind(clean(article_talk_views, "Article talk", "Most views"),
                         clean(user_talk_views, "User talk", "Most views"))
  pageview_data$url <- paste0("https://en.wikipedia.org/wiki/", pageview_data$title, "?oldid=", pageview_data$revision)
  pageview_data <- pageview_data[,c("title", "events", "url", "type", "class")]
  results <- rbind(data, pageview_data)
  
  # Controversial articles
  content <- WikipediR::page_content("en", "wikipedia", page_name = "Wikipedia:List of controversial issues",
                                     as_wikitext = TRUE)$parse$wikitext
  content <- stri_split_lines1(unlist(content))
  content <- content[which(grepl(x = content, pattern = "==="))[1]:length(content)]
  links <- stri_extract_first_regex(str = content, pattern = "\\[{2}.*?\\]{2}")
  links <- gsub(x = links[!is.na(links)], pattern = "(\\|.*|\\[{2}|\\]{2})", replacement = "")
  links <- links[!grepl(x = links, pattern = ":", fixed = TRUE)]
  articles <- paste0("Talk:", sample(links, 30))
  article_ids <- unlist(lapply(articles, function(page){
    cat(".")
    content <- try({
      content <- page_content("en", "wikipedia", page_name = page)
    }, silent = TRUE)
    if("try-error" %in% class(content)){
      return(NA)
    }
    return(content$parse$revid)
  }))
  controversial_articles <- data.frame(title = articles, events = NA,
                                       url = paste0("https://en.wikipedia.org/wiki/",
                                                    gsub(x = articles, pattern = " ", replacement = "_"),
                                                    "?oldid=", article_ids),
                                       type = "Article talk",
                                       class = "Controversial",
                                       stringsAsFactors = FALSE)
  results <- rbind(results, controversial_articles)
  
  dispute_boards <- c("Wikipedia:Administrators'_noticeboard", "Wikipedia:Administrators'_noticeboard/Incidents",
                      "Wikipedia:Arbitration/Requests/Enforcement", "Wikipedia:Biographies_of_living_persons/Noticeboard",
                      "Wikipedia:Fringe_theories/Noticeboard", "Wikipedia:No_original_research/Noticeboard",
                      "Wikipedia:Reliable_sources/Noticeboard")
  dispute_ids <- unlist(lapply(dispute_boards, function(page){
    cat(".")
    content <- try({
      content <- page_content("en", "wikipedia", page_name = page)
    }, silent = TRUE)
    if("try-error" %in% class(content)){
      return(NA)
    }
    return(content$parse$revid)
  }))
  dispute_articles <- data.frame(title = dispute_boards, events = NA,
                                 url = paste0("https://en.wikipedia.org/wiki/",
                                              gsub(x = dispute_boards, pattern = " ", replacement = "_"),
                                              "?oldid=", dispute_ids),
                                 type = "Wikipedia",
                                 class = "Dispute resolution",
                                 stringsAsFactors = FALSE)
  results <- rbind(results, dispute_articles)
  write.table(results, file = file.path(getwd(),"/data/selected_articles.tsv"), row.names = FALSE, quote = FALSE, sep = "\t")
}

main()
