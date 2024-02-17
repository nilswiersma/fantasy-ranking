const HLTV_STATS_BASE = 'https://www.hltv.org/stats';
const HLTV_MONEY_BASE = 'https://www.hltv.org/fantasy';
const HLTV_SEARCH_BASE = 'https://www.hltv.org/search';

const HLTV_STATS_URL_REGEX = /a href="\/events\/(?<eventStatsId>.*?)\/(?<eventStatsName>.*?)"/gm;

// wait for ~300ms between requests to prevent timeouts from hltv.org
var holdoffUntil = new Date();

function postToOpener(msg) {
  if (!!window.opener) {
    window.opener.postMessage(msg, '*');
  }
}

function checkHoldoff(cmd) {
  if (new Date() < holdoffUntil) {
    postToOpener({'cmd': cmd.cmd, 'status': 'holdoff'});
    return false;
  }
  holdoffUntil = new Date().setMilliseconds(new Date().getMilliseconds() + 300);
  return true;
}

function statsRequestHandler(event) {
    let cmd = event.data;
    console.info(`received command`);
    console.info(cmd);

    if (!checkHoldoff(cmd)) { return }

    if (cmd.cmd == 'getPlayerStats') {
      let url = `${HLTV_STATS_BASE}/players?${new URLSearchParams(cmd.filter).toString()}`;
      console.debug(`fetching ${url}`);
      fetch(url).then((resp) => resp.text())
      .then((html) => postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'filter': cmd.filter,
        'playerStatsHtml': html
      }));

    } else if (cmd.cmd == 'getMoneyStats') {
      let url = `${HLTV_MONEY_BASE}/${cmd.fantasyInfo.eventId}/leagues/${cmd.fantasyInfo.leagueId}/join/json`;
      console.debug(`fetching ${url}`);
      fetch(url).then((resp) => resp.json())
      .then((data) => postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'fantasyInfo': cmd.fantasyInfo,
        'playerStatsJson': data['moneyDraftData']['teams']
      }));

    } else if (cmd.cmd == 'getSearch') {
      let url = `${HLTV_SEARCH_BASE}?${new URLSearchParams(cmd.query).toString()}`;
      console.debug(`fetching ${url}`);
      fetch(url).then((resp) => resp.json())
      .then((data) => postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'query': cmd.query,
        'json': data
      }));

    } else if (cmd.cmd == 'findStatsUrls') {
      postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'url': window.location.href,
        'json': [...document.querySelector('html')
          .innerHTML
          .matchAll(HLTV_STATS_URL_REGEX)]
          .map((m) => m.groups)
      });

    } else {
      console.warn(`unknown cmd ${cmd.cmd}`);
    }
}

if (!!window.opener) {
    window.addEventListener("message", statsRequestHandler, false);
    console.info('waiting for requests from opener');
    postToOpener({'cmd': 'ping', 'status': 'pong'});
} else {
    console.debug('no opener found, not adding handler!');
}