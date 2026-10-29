import { expect, test, type Page } from '@playwright/test'

const MAX_ROLLS = 200

function rollButton(page: Page) {
  return page.getByRole('button', { name: 'Roll the die' })
}

function winnerBanner(page: Page) {
  return page.getByRole('status').filter({ hasText: / wins!$/ })
}

test('two players in separate browsers play a game to the end', async ({ browser }) => {
  const contextA = await browser.newContext()
  const contextB = await browser.newContext()
  const pageA = await contextA.newPage()
  const pageB = await contextB.newPage()

  await pageA.goto('/')
  const createForm = pageA.getByRole('form', { name: 'Create a game' })
  await createForm.getByLabel('Your name').fill('Alice')
  await createForm.getByLabel('Players').selectOption('2')
  // Little money and no salary make bankruptcy, and so the end of the game, come within a few rolls.
  await createForm.getByLabel('Starting money').fill('200')
  await createForm.getByLabel('Salary').fill('0')
  await createForm.getByRole('button', { name: 'Create game' }).click()

  await expect(pageA.getByText('1/2 players joined')).toBeVisible()
  const inviteLink = await pageA.getByLabel('Invite link').inputValue()

  await pageB.goto(inviteLink)
  const joinForm = pageB.getByRole('form', { name: 'Join a game' })
  await joinForm.getByLabel('Your name').fill('Bob')
  await joinForm.getByRole('button', { name: 'Join game' }).click()

  for (const page of [pageA, pageB]) {
    await expect(page.getByRole('listitem', { name: 'Player Alice' })).toBeVisible()
    await expect(page.getByRole('listitem', { name: 'Player Bob' })).toBeVisible()
    await expect(page.getByRole('region', { name: 'Invite players' })).toBeHidden()
  }

  let rolls = 0
  while (!(await winnerBanner(pageA).isVisible()) || !(await winnerBanner(pageB).isVisible())) {
    expect(rolls, 'the game should end within the roll cap').toBeLessThan(MAX_ROLLS)
    const roller = await firstEnabledRoll([pageA, pageB])
    if (roller !== null) {
      await rollButton(roller).click()
      rolls += 1
    }
  }

  const winnerA = await winnerBanner(pageA).textContent()
  await expect(winnerBanner(pageB)).toHaveText(winnerA ?? '')
  expect(winnerA).toMatch(/^(Alice|Bob) wins!$/)
  for (const page of [pageA, pageB]) {
    await expect(page.getByRole('region', { name: 'Players' }).getByText('Bankrupt')).toHaveCount(1)
  }

  await contextA.close()
  await contextB.close()
})

// Waits until one of the pages may roll: right after a turn both buttons are disabled until the
// broadcast state reaches each page.
async function firstEnabledRoll(pages: Page[]): Promise<Page | null> {
  const deadline = Date.now() + 5_000
  while (Date.now() < deadline) {
    for (const page of pages) {
      if (await rollButton(page).isEnabled()) return page
      if (await winnerBanner(page).isVisible()) return null
    }
    await pages[0].waitForTimeout(50)
  }
  throw new Error('No player could roll the die within 5 seconds')
}
