const HLTV_STATS_BASE = 'https://www.hltv.org/stats';
const HLTV_MONEY_BASE = 'https://www.hltv.org/fantasy';

// wait for ~300ms between requests to prevent bans
var holdoffUntil = new Date();

function postToOpener(msg) {
  if (!!window.opener) {
    window.opener.postMessage(msg, '*');
  }
}

function checkHoldoff() {
  if (new Date() < holdoffUntil) {
    postToOpener({'cmd': cmd.cmd, 'status': 'holdoff'});
    return false;
  }
  holdoffUntil = new Date().setMilliseconds(new Date().getMilliseconds() + 300);
  return true;
}

function statsRequestHandler(event) {
    let cmd = event.data;

    console.log(cmd);

    if (cmd.cmd == 'getPlayerStats') {
      if (!checkHoldoff()) { return }
      fetch(`${HLTV_STATS_BASE}/players?${new URLSearchParams(cmd.filter).toString()}`)
      .then((resp) => resp.text())
      .then((html) => postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'filter': cmd.filter,
        'playerStatsHtml': html
      }));
    } else if (cmd.cmd == 'getMoneyStats') {
      if (!checkHoldoff()) { return }
      console.log(`${HLTV_MONEY_BASE}/${cmd.fantasyInfo.eventId}/leagues/${cmd.fantasyInfo.leagueId}/join/json`);
      fetch(`${HLTV_MONEY_BASE}/${cmd.fantasyInfo.eventId}/leagues/${cmd.fantasyInfo.leagueId}/join/json`)
      .then((resp) => resp.json())
      .then((data) => postToOpener({
        'cmd': cmd.cmd,
        'status': 'ok',
        'fantasyInfo': cmd.fantasyInfo,
        'playerStatsJson': data['moneyDraftData']['teams']
      }));
    } else {
      console.log(`unknown cmd ${cmd.cmd}`);
    }
}

if (!!window.opener) {
    window.addEventListener("message", statsRequestHandler, false);
    console.log('waiting for requests from opener');
    postToOpener('ping');
} else {
    console.log('no opener found!');
}
