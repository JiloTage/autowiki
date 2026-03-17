// Auto-Wiki - D3.js Force-directed Graph Visualization
(function() {
  'use strict';

  const GRAPH_DATA_URL = 'db/graph.json';

  function initGraph(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight || 500;

    const svg = d3.select(container)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height]);

    // Zoom behavior
    const g = svg.append('g');
    const zoom = d3.zoom()
      .scaleExtent([0.3, 4])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    // Tooltip
    const tooltip = d3.select(container)
      .append('div')
      .attr('class', 'graph-tooltip')
      .style('opacity', 0)
      .style('display', 'none');

    // Load data: prefer inline data (for file:// protocol), fallback to fetch
    if (window.__GRAPH_DATA__) {
      renderGraph(window.__GRAPH_DATA__, g, width, height, tooltip);
    } else {
      fetch(GRAPH_DATA_URL)
        .then(r => r.json())
        .then(data => renderGraph(data, g, width, height, tooltip))
        .catch(err => {
          container.innerHTML = '<p style="text-align:center;color:#72777d;padding:40px;">グラフデータを読み込めません</p>';
          console.error('Graph load error:', err);
        });
    }
  }

  function renderGraph(data, g, width, height, tooltip) {
    if (!data.nodes || data.nodes.length === 0) {
      return;
    }

    // Arrow marker
    g.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 20)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#a2a9b1');

    // Force simulation
    const simulation = d3.forceSimulation(data.nodes)
      .force('link', d3.forceLink(data.links)
        .id(d => d.id)
        .distance(100))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Links
    const link = g.append('g')
      .selectAll('line')
      .data(data.links)
      .join('line')
      .attr('stroke', '#c8ccd1')
      .attr('stroke-width', 1.5)
      .attr('marker-end', 'url(#arrowhead)');

    // Nodes
    const node = g.append('g')
      .selectAll('g')
      .data(data.nodes)
      .join('g')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }));

    // Node circles
    node.append('circle')
      .attr('r', d => d.is_root ? 12 : 8)
      .attr('fill', d => d.is_root ? '#0645ad' : '#36c')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer');

    // Node labels
    node.append('text')
      .text(d => d.title)
      .attr('x', 0)
      .attr('y', d => (d.is_root ? 12 : 8) + 14)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('font-family', 'var(--font-sans)')
      .attr('fill', '#202122')
      .each(function(d) {
        // Truncate long titles
        const maxLen = 20;
        if (d.title.length > maxLen) {
          d3.select(this).text(d.title.substring(0, maxLen) + '...');
        }
      });

    // Hover events
    node
      .on('mouseover', (event, d) => {
        tooltip
          .style('display', 'block')
          .style('opacity', 1)
          .html(`<strong>${d.title}</strong>${d.summary ? '<br>' + d.summary : ''}`)
          .style('left', (event.offsetX + 10) + 'px')
          .style('top', (event.offsetY - 10) + 'px');
      })
      .on('mouseout', () => {
        tooltip.style('opacity', 0).style('display', 'none');
      })
      .on('click', (event, d) => {
        if (d.url) window.location.href = d.url;
      });

    // Simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${d.x},${d.y})`);
    });
  }

  // Export
  window.AutoWikiGraph = { init: initGraph };
})();
