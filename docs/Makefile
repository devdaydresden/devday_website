SVG_DIAGRAMS := $(patsubst %.puml,%.svg,$(wildcard *.puml))

all: $(SVG_DIAGRAMS)

$(SVG_DIAGRAMS): %.svg: %.puml
	plantuml -tsvg $<

clean:
	rm -f $(SVG_DIAGRAMS)

.PHONY: all clean
