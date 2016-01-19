library(wmf)
library(data.table)
library(magrittr)
options(scipen = 500)
dir.create("./data/", showWarnings = FALSE)

# Retrieve logs for a sub-sample of en.wiki talk/discussion pages, parse them with the python parser in ./parser,
# Read the resulting (parsed) data in and scrub it.
main <- function(){
  
  cat(paste("New run:\t", Sys.time(), "\n"), file = "retriever.log", append = TRUE)
  
  # Grab all the talkpage pageIDs in the article and user talk namespaces. Also grab the namespaces so we can sample
  # in a stratified fashion.
  data <- wmf::mysql_read("SELECT page_id, page_title, page_namespace FROM page WHERE page_namespace IN(1,3)",
                          "enwiki") %>%
    as.data.table
  cat(paste("Pages retrieved:\t", nrow(data)), file = "retriever.log", append = TRUE)
  
  # Sample out 10k pages from each namespace
  data <- data[, j = { .SD[sample(1:.N, 10000)]}, "page_namespace"]
  
  # Can't be forgetting the noticeboards!
  noticeboards <- c("Requests_for_arbitration/Arbitration_Committee_noticeboard",
                    "Reliable_sources/Noticeboard",
                    "Biographies_of_living_persons/Noticeboard",
                    "Administrators\\'_noticeboard",
                    "Administrators\\'_noticeboard/Incidents")
  noticeboards <- paste0("'", paste(c(noticeboards), collapse = "', '"), "'")
  noticeboard_data <- wmf::mysql_read(paste0("SELECT page_id, page_title, page_namespace FROM page WHERE page_namespace = 4
                                              AND page_title IN (", noticeboards, ")"), "enwiki")
  
  results <- as.data.frame(rbind(data, noticeboard_data))
  write.table(results, file = file.path(getwd(),"/data/parser_input.tsv"), row.names = FALSE, col.names = FALSE, quote = FALSE, sep = "\t")
}

main()
