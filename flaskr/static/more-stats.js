var event_link = document.querySelector('.textBox').querySelector('a').href;
console.log(event_link);
var money_league = document.querySelectorAll('.money-league')[1];
if (money_league.innerText != "HLTV x Roobet league") {
    // Probably does not matter as all of them will use the same money value for players
    console.warn('Expected HLTV x Roobet league, found <' + money_league.innerText +'>')
}
var money_link = money_league.querySelector('a').href.replace("league", "leagues") + "/join/json";
console.log(money_link);

// Get the team links from the event page
var team_links = [];
await fetch(event_link)
.then(function(resp) {
    return resp.text()
})
.then(function(html) {
    var parser = new DOMParser();
    var parsed = parser.parseFromString(html, "text/html");
    Array.from(parsed.querySelector('.teams-attending').children).forEach(function(v, k) {
        var team_name = v.querySelector('.team-name').querySelector('.text').innerHTML;
        var teamLink = v.querySelector('.team-name').querySelector('a').href;
        var team_link_stats = teamLink.replace("team/", "stats/teams/players/"); 
        console.log(team_name + ': ' + team_link_stats);
        team_links.push({'team_name': team_name, 'team_link_stats': team_link_stats});
    });
});
sessionStorage.setItem('team_links', JSON.stringify(team_links));

// Get the money data which also contains last 6 month stats
var fantasy_data = null;
var money_data;
await fetch(money_link)
.then(function(resp) {
    return resp.json()
})
.then(function(data) {
    money_data = data;
});
sessionStorage.setItem('money_data', JSON.stringify(money_data));

// Get the 1 and 3 month filters from a stat page
var time_filters;
await fetch(team_links[0].team_link_stats)
.then(function(resp) {
    return resp.text();
})
.then(function(html) {
    var parser = new DOMParser();
    var parsed = parser.parseFromString(html, "text/html");

    time_filters = Array.from(parsed.querySelector('.stats-sub-navigation-simple-filter-time').children).slice(1,3); // 1 month and 3 months
    time_filters[0] = time_filters[0].attributes['data-link'].textContent.split('?')[1]
    time_filters[1] = time_filters[1].attributes['data-link'].textContent.split('?')[1]
})
console.log(time_filters);

// Collect the 1 month and 3 month stats for each player in each team
var request_delay_ms = 1000;
var collect = [];
var collect2 = {};
delay = ms => new Promise(res => setTimeout(res, ms));
forLoop = async _ => {
    console.log('grabbing data')
    for (team of team_links) {
        for (time_filter of time_filters) {

            console.log(team.team_link_stats + '?' + time_filter);

            await fetch(team.team_link_stats + '?' + time_filter)
            .then(function(resp) {
                return resp.text()
            })
            .then(function(html) {
                var parser = new DOMParser();
                var parsed = parser.parseFromString(html, "text/html");
                // console.log(parsed.querySelector('.player-ratings-table'));
                Array.from(parsed.querySelector('.player-ratings-table').querySelector('tbody').querySelectorAll('tr')).forEach(function(player_row, k){
                    // console.log(player_row);
                    var stats = [team.team_name, time_filter];
                    stats = stats.concat(player_row.innerText.split('\n'));
                    console.log(stats);
                    collect.push(stats);

                    var stats2 = player_row.innerText.split('\n');
                    var playerName = stats2[1].trim();

                    if (!(playerName in collect2)) {
                      collect2[playerName] = {
                        '1-maps': parseInt(stats2[2].trim()),
                        '1-rounds': parseInt(stats2[3].trim()),
                        '1-kd_diff': parseInt(stats2[4].trim()),
                        '1-kd_ratio': parseFloat(stats2[5].trim()),
                        '1-rating': parseFloat(stats2[6].trim()),
                      };
                    } else {
                      collect2[playerName]['3-maps'] = parseInt(stats2[2].trim());
                      collect2[playerName]['3-rounds'] = parseInt(stats2[3].trim());
                      collect2[playerName]['3-kd_diff'] = parseInt(stats2[4].trim());
                      collect2[playerName]['3-kd_ratio'] = parseFloat(stats2[5].trim());
                      collect2[playerName]['3-rating'] = parseFloat(stats2[6].trim());
                    }
                });
            });

            await delay(request_delay_ms);
        }
    }

}
await forLoop();
console.log('data grabbed in collect and collect2');
console.log('sending collect2 to opener');
if (!!window.opener) {
    window.opener.postMessage(collect2, '*');
    console.log(`to resend, use`);
    console.log(`window.opener.postMessage(collect2, '*');`);
} else {
    console.log('no opener found!');
}
