library(shiny)

shinyUI(fluidPage(
  titlePanel("Everyone Loves Data Input!"),
    mainPanel(
      tags$textarea(id="section_title", rows=1, cols=40, "Section title"),
      tags$textarea(id="section_title", rows=5, cols=40, "Previous comment (if applicable)"),
      tags$textarea(id="section_title", rows=5, cols=40, "Comnment"),
      submitButton(text = "Save", icon = icon("check"), width = NULL)
    )
  )
)
